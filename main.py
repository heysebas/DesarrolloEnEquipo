import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from tkinter import ttk
import mysql.connector
from datetime import datetime, timedelta
import random


# Funciones para manejo de datos

def get_last_6_months_data():
    """Obtiene las fechas de los últimos 6 meses."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    return start_date, end_date


def load_data():
    """Carga datos de la base de datos para los últimos 6 meses."""
    start_date, end_date = get_last_6_months_data()
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='0908',
        database='periodicos'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, cantidad, nombre FROM records WHERE fecha BETWEEN %s AND %s", (start_date, end_date))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data


def show_last_6_months_data():
    """Muestra los datos de los últimos 6 meses en una nueva ventana."""
    data = load_data()

    # Crear una nueva ventana
    new_window = tk.Toplevel(root)
    new_window.title("Datos de los Últimos 6 Meses")

    # Obtener las fechas para los últimos 6 meses
    columns = ['Nombre'] + [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(180)][::-1]
    tree = show_table(new_window, columns)

    # Agrupar datos por nombre
    grouped_data = {}
    for fecha, cantidad, nombre in data:
        if nombre not in grouped_data:
            grouped_data[nombre] = [''] * 180  # Inicializa la lista con celdas vacías
        index = (datetime.now() - fecha).days
        if index < 180:
            grouped_data[nombre][179 - index] = cantidad

    # Insertar datos en el árbol
    for nombre, cantidades in grouped_data.items():
        tree.insert("", "end", values=[nombre] + cantidades)

    # Ajustar el tamaño de las columnas
    for col in columns:
        tree.column(col, width=100)


def show_table(parent, columns):
    """Muestra una tabla en la ventana proporcionada."""
    tree = ttk.Treeview(parent, columns=columns, show='headings')

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    tree.pack(expand=True, fill='both')
    return tree


def load_data_from_db():
    """Carga datos desde la base de datos en la tabla principal."""
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

        # Limpiar el árbol antes de insertar nuevos datos
        for row in tree.get_children():
            tree.delete(row)

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
    """Obtiene las fechas de los últimos 7 días."""
    today = datetime.now()
    return [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]


def populate_data():
    """Genera datos de prueba para 6 meses."""
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
    """Agrega un nombre a la tabla."""
    name = name_entry.get()
    if name:
        tree.insert("", "end", values=[name] + [''] * 7)


def add_number():
    """Agrega un número a la fecha seleccionada."""
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

        else:
            messagebox.showwarning("Advertencia", "No se puede modificar el valor de la fecha actual.")


def upload_file():
    """Sube un archivo CSV a la base de datos."""
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
    """Guarda los datos de la tabla en la base de datos."""
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
                        ON DUPLICATE KEY UPDATE cantidad = VALUES(cantidad)  -- Actualizar si ya existe
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

# Marco principal para organización
main_frame = tk.Frame(root)
main_frame.pack(expand=True, fill='both', padx=10, pady=10)

# Campo de entrada para agregar nombres
name_label = tk.Label(main_frame, text="Ingrese el nombre:")
name_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

name_entry = tk.Entry(main_frame)
name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

# Botón para agregar nombre
add_button = tk.Button(main_frame, text="Agregar nombre", command=add_name)
add_button.grid(row=0, column=2, padx=5, pady=5, sticky="w")

# Campo de entrada para agregar un número
number_label = tk.Label(main_frame, text="Ingrese un número para la fecha seleccionada:")
number_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")

number_entry = tk.Entry(main_frame)
number_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

# Botón para agregar número
add_number_button = tk.Button(main_frame, text="Agregar número", command=add_number)
add_number_button.grid(row=1, column=2, padx=5, pady=5, sticky="w")

# Botón para subir archivo CSV
upload_button = tk.Button(main_frame, text="Subir CSV", command=upload_file)
upload_button.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="we")

# Botón para guardar en la base de datos
save_button = tk.Button(main_frame, text="Guardar en DB", command=save_to_db)
save_button.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="we")

# Botón para mostrar datos de los últimos 6 meses
show_button = tk.Button(main_frame, text="Mostrar últimos 6 meses", command=show_last_6_months_data)
show_button.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="we")

# Crear el árbol para mostrar los datos
columns = ['Nombre'] + get_last_7_days()
tree = ttk.Treeview(main_frame, columns=columns, show='headings')

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

tree.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")

# Cargar datos iniciales desde la base de datos
load_data_from_db()

root.mainloop()
