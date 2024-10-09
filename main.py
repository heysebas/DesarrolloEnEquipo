import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import numpy as np

# Funciones para manejo de datos

def get_last_6_months_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    return start_date, end_date

def load_data():
    start_date, end_date = get_last_6_months_data()
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='0908',
        database='periodicos'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, cantidad FROM records WHERE fecha BETWEEN %s AND %s", (start_date, end_date))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def calculate_average(data):
    return np.mean([x[1] for x in data])

def check_below_threshold(daily_count, average_count):
    threshold = average_count * 0.8
    return daily_count < threshold

def coefficient_of_variation(data):
    mean = np.mean(data)
    std_dev = np.std(data)
    return (std_dev / mean) * 100 if mean != 0 else 0

def notify_if_below_threshold(daily_count, average_count, nombre):
    if check_below_threshold(daily_count, average_count):
        messagebox.showwarning("Advertencia", f"{nombre} ha subido menos artículos de los esperados.")

def load_data_from_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='0908',
            database='periodicos'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, fecha, cantidad FROM records")
        results = cursor.fetchall()

        # Agrupar los resultados por nombre
        data = {}
        for nombre, fecha, cantidad in results:
            if nombre not in data:
                data[nombre] = [''] * 7
            fecha_str = fecha.strftime("%Y-%m-%d")
            index = get_last_7_days().index(fecha_str) if fecha_str in get_last_7_days() else -1
            if index >= 0:
                data[nombre][index] = cantidad

        # Insertar los datos en el árbol
        for nombre, cantidades in data.items():
            tree.insert("", "end", values=[nombre] + cantidades)

    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron cargar los datos:\n{e}")
    finally:
        if conn:
            conn.close()

def get_last_7_days():
    today = datetime.now()
    return [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

def show_table():
    last_7_days = get_last_7_days()
    columns = ['nombre'] + last_7_days
    tree = ttk.Treeview(table_frame, columns=columns, show='headings')

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    tree.pack(expand=True, fill='both')
    return tree

def load_all_data_from_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='0908',
            database='periodicos'
        )
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, fecha, cantidad FROM records")
        results = cursor.fetchall()

        data = {}
        fechas = set()
        for nombre, fecha, cantidad in results:
            if nombre not in data:
                data[nombre] = {}
            fecha_str = fecha.strftime("%Y-%m-%d")
            data[nombre][fecha_str] = cantidad
            fechas.add(fecha_str)

        fechas = sorted(fechas)

        show_all_days_table(data, fechas)

    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron cargar los datos:\n{e}")
    finally:
        if conn:
            conn.close()

def show_all_days_table(data, fechas):
    columns = ['nombre'] + fechas
    tree = ttk.Treeview(table_frame, columns=columns, show='headings')

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    for nombre, cantidades in data.items():
        values = [nombre] + [cantidades.get(fecha, '') for fecha in fechas]
        tree.insert("", "end", values=values)

    tree.pack(expand=True, fill='both')
    return tree

def add_name():
    name = name_entry.get()
    if name:
        tree.insert("", "end", values=[name] + [''] * 7)

def add_number():
    selected_item = tree.selection()
    if selected_item:
        current_date = datetime.now().strftime("%Y-%m-%d")
        values = tree.item(selected_item)['values']

        if current_date not in values:
            number = number_entry.get()
            if number.isdigit():
                current_index = get_last_7_days().index(current_date) + 1
                values[current_index] = number
                tree.item(selected_item, values=values)

                daily_count = int(number)
                avg_count = calculate_average(load_data())
                notify_if_below_threshold(daily_count, avg_count, values[0])
        else:
            messagebox.showwarning("Advertencia", "No se puede modificar el valor de la fecha actual.")

def upload_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        try:
            df = pd.read_csv(file_path)
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='0908',
                database='periodicos'
            )
            cursor = conn.cursor()

            for index, row in df.iterrows():
                nombre = row['nombre']
                for date_col in row.index[1:]:
                    fecha = datetime.strptime(date_col, '%d-%m-%Y').date()
                    cantidad = row[date_col]
                    cursor.execute("""
                        INSERT INTO records (nombre, fecha, cantidad)
                        VALUES (%s, %s, %s)
                    """, (nombre, fecha, cantidad))

            conn.commit()
            messagebox.showinfo("Éxito", "Datos subidos correctamente.")
            load_data_from_db()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
        finally:
            if conn:
                conn.close()

def save_to_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='0908',
            database='periodicos'
        )
        cursor = conn.cursor()

        for child in tree.get_children():
            values = tree.item(child)['values']
            nombre = values[0]
            fechas = values[1:]

            for i, fecha in enumerate(get_last_7_days()):
                if fechas[i]:
                    cursor.execute("""
                        INSERT INTO records (nombre, fecha, cantidad)
                        VALUES (%s, %s, %s)
                    """, (nombre, fecha, fechas[i]))

        conn.commit()
        messagebox.showinfo("Éxito", "Datos guardados en la base de datos.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron guardar los datos:\n{e}")
    finally:
        if conn:
            conn.close()

# Configuración de la ventana principal
root = tk.Tk()
root.title("Análisis de Artículos de Noticias")
root.geometry("1800x900")

# Crear marcos para organizar la interfaz
input_frame = ttk.Frame(root, padding="10")
input_frame.pack(fill='x')

table_frame = ttk.Frame(root, padding="10")
table_frame.pack(expand=True, fill='both')

button_frame = ttk.Frame(root, padding="10")
button_frame.pack(fill='x')

# Campo de entrada para agregar nombres
name_label = ttk.Label(input_frame, text="Ingrese el nombre:")
name_label.grid(row=0, column=0, padx=5, pady=5, sticky='w')

name_entry = ttk.Entry(input_frame)
name_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

# Botón para agregar nombre
add_button = ttk.Button(input_frame, text="Agregar nombre", command=add_name)
add_button.grid(row=0, column=2, padx=5, pady=5)

# Campo de entrada para agregar un número
number_label = ttk.Label(input_frame, text="Ingrese un número para la fecha seleccionada:")
number_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')

number_entry = ttk.Entry(input_frame)
number_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

# Botón para agregar número
add_number_button = ttk.Button(input_frame, text="Agregar número", command=add_number)
add_number_button.grid(row=1, column=2, padx=5, pady=5)

# Botones para subir archivo, guardar en BD y cargar datos
upload_button = ttk.Button(button_frame, text="Subir archivo CSV", command=upload_file)
upload_button.grid(row=0, column=0, padx=5, pady=5)

save_button = ttk.Button(button_frame, text="Guardar en la base de datos", command=save_to_db)
save_button.grid(row=0, column=1, padx=5, pady=5)

load_button = ttk.Button(button_frame, text="Cargar últimos 7 días", command=load_data_from_db)
load_button.grid(row=0, column=2, padx=5, pady=5)

all_days_button = ttk.Button(button_frame, text="Mostrar todos los días", command=load_all_data_from_db)
all_days_button.grid(row=0, column=3, padx=5, pady=5)

# Mostrar la tabla inicial
tree = show_table()

# Iniciar la aplicación
root.mainloop()
