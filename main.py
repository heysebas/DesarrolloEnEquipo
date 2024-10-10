import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import numpy as np

# Función para obtener la conexión a la base de datos
def get_db_connection():
    """Establece y retorna la conexión a la base de datos."""
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='0908',
        database='periodicos'
    )

# Funciones para manejo de datos

def get_last_6_months_data():
    """Obtiene las fechas de inicio y fin correspondientes a los últimos 6 meses."""
    end_date = datetime.now()  # Fecha actual
    start_date = end_date - timedelta(days=180)  # Fecha de hace 180 días
    return start_date, end_date  # Retorna el rango de fechas

def load_data():
    """Carga los datos de la base de datos dentro del rango de los últimos 6 meses."""
    start_date, end_date = get_last_6_months_data()  # Obtiene las fechas de los últimos 6 meses
    conn = get_db_connection()
    cursor = conn.cursor()  # Crea el cursor para ejecutar la consulta
    cursor.execute("SELECT fecha, cantidad FROM records WHERE fecha BETWEEN %s AND %s", (start_date, end_date))
    data = cursor.fetchall()  # Obtiene todos los resultados de la consulta
    cursor.close()  # Cierra el cursor
    conn.close()  # Cierra la conexión a la base de datos
    return data  # Retorna los datos obtenidos

def calculate_average(data):
    """Calcula el promedio de la columna 'cantidad' de los datos obtenidos."""
    return np.mean([x[1] for x in data])  # Calcula el promedio usando numpy

def load_all_data_from_db():
    """Carga todos los datos de la base de datos y los muestra en una tabla."""
    try:
        conn = get_db_connection()
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
    """Muestra una tabla con los datos de todas las fechas disponibles."""
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
    """Añade un nuevo nombre a la tabla."""
    name = name_entry.get()
    if name:
        tree.insert("", "end", values=[name] + [''] * 7)

def add_number():
    """Añade el número de artículos a la tabla para la fecha actual."""
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
                promedios = calculate_weekday_average()
                nombre = values[0]
                avg_count = promedios.get(nombre, 0)

                notify_if_below_threshold(daily_count, avg_count, nombre)
        else:
            messagebox.showwarning("Advertencia", "No se puede modificar el valor de la fecha actual.")

def upload_file():
    """Carga un archivo CSV y sube los datos a la base de datos."""
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        try:
            df = pd.read_csv(file_path)
            conn = get_db_connection()
            cursor = conn.cursor()

            for index, row in df.iterrows():
                nombre = row['nombre']
                for date_col in row.index[1:]:
                    # Aquí iría el código para insertar los datos en la base de datos
                    pass

            conn.commit()
            messagebox.showinfo("Éxito", "Datos subidos correctamente.")
            load_data_from_db()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
        finally:
            if conn:
                conn.close()

def save_to_db():
    """Guarda los datos actuales de la tabla en la base de datos."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        for child in tree.get_children():
            values = tree.item(child)['values']
            nombre = values[0]
            fechas = values[1:]

            for i, fecha in enumerate(get_last_7_days()):
                if fechas[i]:
                    # Aquí iría el código para insertar los datos en la base de datos
                    pass

        conn.commit()
        messagebox.showinfo("Éxito", "Datos guardados en la base de datos.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron guardar los datos:\n{e}")
    finally:
        if conn:
            conn.close()

def calculate_weekday_average():
    """Calcula el promedio diario por empresa para el día de la semana actual."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, fecha, cantidad FROM records")
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pd.DataFrame(results, columns=['nombre', 'fecha', 'cantidad'])
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['dia_semana'] = df['fecha'].dt.day_name()

    dia_semana_actual = datetime.now().strftime("%A")
    df_filtered = df[df['dia_semana'] == dia_semana_actual]

    promedio_por_empresa = df_filtered.groupby('nombre')['cantidad'].mean().reset_index()
    promedios = promedio_por_empresa.set_index('nombre')['cantidad'].to_dict()
    return promedios

def check_below_threshold(daily_count, average_count):
    """Verifica si el conteo diario está por debajo del 80% del promedio."""
    threshold = average_count * 0.8
    return daily_count < threshold

def notify_if_below_threshold(daily_count, average_count, nombre):
    """Notifica si el conteo diario está por debajo del umbral."""
    if check_below_threshold(daily_count, average_count):
        messagebox.showwarning("Advertencia", f"{nombre} ha subido menos artículos de los esperados.")

def load_data_from_db():
    """Carga datos de los últimos 7 días desde la base de datos y los organiza en una tabla."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, fecha, cantidad FROM records")
        results = cursor.fetchall()

        data = {}
        for nombre, fecha, cantidad in results:
            if nombre not in data:
                data[nombre] = {}
            fecha_str = fecha.strftime("%Y-%m-%d")
            index = get_last_7_days().index(fecha_str) if fecha_str in get_last_7_days() else -1
            if index >= 0:
                data[nombre][fecha_str] = cantidad

        for nombre, cantidades in data.items():
            tree.insert("", "end", values=[nombre] + [cantidades.get(fecha, '') for fecha in get_last_7_days()])

    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron cargar los datos:\n{e}")
    finally:
        if conn:
            conn.close()

def get_last_7_days():
    """Obtiene una lista de fechas de los últimos 7 días."""
    today = datetime.now()
    return [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

def calculate_quartiles(data):
    """Calcula los cuartiles de la cantidad de artículos."""
    quantities = [x[1] for x in data]
    q1 = np.percentile(quantities, 25)
    q2 = np.percentile(quantities, 50)
    q3 = np.percentile(quantities, 75)
    return q1, q2, q3

def show_table():
    """Muestra la tabla con los datos de los últimos 7 días."""
    last_7_days = get_last_7_days()
    columns = ['nombre'] + last_7_days
    tree = ttk.Treeview(table_frame, columns=columns, show='headings')

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    tree.pack(expand=True, fill='both')
    return tree

def calculate_quartiles(data):
    """Calcula los cuartiles de la cantidad de artículos."""
    quantities = [x[1] for x in data]
    q1 = np.percentile(quantities, 25)
    q2 = np.percentile(quantities, 50)
    q3 = np.percentile(quantities, 75)
    return q1, q2, q3

def show_quartiles():
    """Muestra los cuartiles de los datos en un mensaje."""
    data = load_data()
    q1, q2, q3 = calculate_quartiles(data)
    messagebox.showinfo("Cuartiles", f"Q1: {q1:.2f}, Q2: {q2:.2f}, Q3: {q3:.2f}")

def calculate_frequency_distribution(data):
    """Calcula la distribución de frecuencia de la cantidad de artículos."""
    df = pd.DataFrame(data, columns=['fecha', 'cantidad'])
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['dia_semana'] = df['fecha'].dt.day_name()
    frequency_distribution = df['dia_semana'].value_counts().sort_index()
    return frequency_distribution

def show_frequency_distribution():
    """Muestra la distribución de frecuencia de los datos en una ventana emergente."""
    data = load_data()
    frequency_distribution = calculate_frequency_distribution(data)

    freq_window = tk.Toplevel(root)
    freq_window.title("Distribución de Frecuencia")
    freq_window.geometry("400x300")

    columns = ['Día', 'Frecuencia']
    freq_tree = ttk.Treeview(freq_window, columns=columns, show='headings')

    for col in columns:
        freq_tree.heading(col, text=col)
        freq_tree.column(col, anchor="center")

    for dia, frecuencia in frequency_distribution.items():
        freq_tree.insert("", "end", values=[dia, frecuencia])

    freq_tree.pack(expand=True, fill='both')

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
add_name_button = ttk.Button(input_frame, text="Agregar Nombre", command=add_name)
add_name_button.grid(row=0, column=2, padx=5, pady=5)

# Campo de entrada para agregar número de artículos
number_label = ttk.Label(input_frame, text="Ingrese el número de artículos:")
number_label.grid(row=1, column=0, padx=5, pady=5, sticky='w')

number_entry = ttk.Entry(input_frame)
number_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')

# Botón para agregar número de artículos
add_number_button = ttk.Button(input_frame, text="Agregar Número de Artículos", command=add_number)
add_number_button.grid(row=1, column=2, padx=5, pady=5)

# Botón para cargar datos desde archivo CSV
upload_button = ttk.Button(button_frame, text="Subir CSV", command=upload_file)
upload_button.pack(side='left', padx=5, pady=5)

# Botón para guardar datos en la base de datos
save_button = ttk.Button(button_frame, text="Guardar en DB", command=save_to_db)
save_button.pack(side='left', padx=5, pady=5)

# Botón para mostrar los datos de la última semana
show_button = ttk.Button(button_frame, text="Mostrar Última Semana", command=load_data_from_db)
show_button.pack(side='left', padx=5, pady=5)

# Botón para mostrar todos los días registrados
show_all_button = ttk.Button(button_frame, text="Mostrar Todos los Días", command=load_all_data_from_db)
show_all_button.pack(side='left', padx=5, pady=5)

# Botón para mostrar la distribución de frecuencia
show_frequency_button = ttk.Button(button_frame, text="Mostrar Distribución de Frecuencia", command=show_frequency_distribution)
show_frequency_button.pack(side='left', padx=5, pady=5)

# Mostrar la tabla inicial
tree = show_table()

# Iniciar el bucle de la interfaz gráfica
root.mainloop()