import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from tkinter import ttk
import numpy as np
import mysql.connector
from datetime import datetime, timedelta
import random


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


def populate_data():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='0908',
        database='periodicos'
    )
    cursor = conn.cursor()

    for i in range(180):  # Generar datos por 6 meses
        date = (datetime.now() - timedelta(days=i)).date()
        nombre = f"Diario {random.choice(['A', 'B', 'C'])}"
        count = random.randint(50, 150)  # Artículos entre 50 y 150
        cursor.execute("INSERT INTO records (nombre, fecha, cantidad) VALUES (%s, %s, %s)", (nombre, date, count))

    conn.commit()
    cursor.close()
    conn.close()


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

                # Comprobar el promedio
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

            # Conectar a la base de datos
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='0908',
                database='periodicos'
            )
            cursor = conn.cursor()

            # Iterar sobre las filas del DataFrame
            for index, row in df.iterrows():
                nombre = row['nombre']
                for date_col in row.index[1:]:  # Ignorar la primera columna (nombre)
                    fecha = datetime.strptime(date_col, '%d-%m-%Y').date()  # Cambia el formato según sea necesario
                    cantidad = row[date_col]
                    cursor.execute("""
                        INSERT INTO records (nombre, fecha, cantidad)
                        VALUES (%s, %s, %s)
                    """, (nombre, fecha, cantidad))

            conn.commit()
            messagebox.showinfo("Éxito", "Datos subidos correctamente.")
            load_data_from_db()  # Recargar los datos en la tabla después de la carga
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

# Marco para la tabla
table_frame = tk.Frame(root)
table_frame.pack(expand=True, fill='both', padx=10, pady=10)

# Campo de entrada para agregar nombres
name_label = tk.Label(root, text="Ingrese el nombre:")
name_label.pack(pady=5)

name_entry = tk.Entry(root)
name_entry.pack(pady=5)

# Botón para agregar nombre
add_button = tk.Button(root, text="Agregar nombre", command=add_name)
add_button.pack(pady=10)

# Campo de entrada para agregar un número
number_label = tk.Label(root, text="Ingrese un número para la fecha seleccionada:")
number_label.pack(pady=5)

number_entry = tk.Entry(root)
number_entry.pack(pady=5)

# Botón para agregar número
add_number_button = tk.Button(root, text="Agregar número", command=add_number)
add_number_button.pack(pady=10)

# Botón para subir el archivo CSV
upload_button = tk.Button(root, text="Subir archivo CSV", command=upload_file)
upload_button.pack(pady=10)

# Botón para guardar en la base de datos
save_button = tk.Button(root, text="Guardar en la base de datos", command=save_to_db)
save_button.pack(pady=10)

# Mostrar la tabla vacía
tree = show_table()

# Cargar datos desde la base de datos al iniciar
load_data_from_db()

# Iniciar la aplicación
root.mainloop()
