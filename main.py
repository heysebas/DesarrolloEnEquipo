import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta
import numpy as np


# Funciones para manejo de datos

# Obtiene las fechas de inicio y fin correspondientes a los últimos 6 meses
def get_last_6_months_data():
    end_date = datetime.now()  # Fecha actual
    start_date = end_date - timedelta(days=180)  # Fecha de hace 180 días
    return start_date, end_date  # Retorna el rango de fechas

# Carga los datos de la base de datos dentro del rango de los últimos 6 meses
def load_data():
    start_date, end_date = get_last_6_months_data()  # Obtiene las fechas de los últimos 6 meses
    # Conexión a la base de datos MySQL
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='0908',
        database='periodicos'
    )
    cursor = conn.cursor()  # Crea el cursor para ejecutar la consulta
    # Ejecuta la consulta SQL para obtener datos entre las fechas determinadas
    cursor.execute("SELECT fecha, cantidad FROM records WHERE fecha BETWEEN %s AND %s", (start_date, end_date))
    data = cursor.fetchall()  # Obtiene todos los resultados de la consulta
    cursor.close()  # Cierra el cursor
    conn.close()  # Cierra la conexión a la base de datos
    return data  # Retorna los datos obtenidos

# Calcula el promedio de la columna "cantidad" de los datos obtenidos
def calculate_average(data):
    return np.mean([x[1] for x in data])  # Calcula el promedio usando numpy

# Calcula el promedio diario por empresa para el día de la semana actualdef load_all_data_from_db():
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
                promedios = calculate_weekday_average()
                nombre = values[0]
                avg_count = promedios.get(nombre, 0)

                notify_if_below_threshold(daily_count, avg_count, nombre)
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
def calculate_weekday_average():
    # Conexión a la base de datos MySQL
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='0908',
        database='periodicos'
    )
    cursor = conn.cursor()  # Crea el cursor para ejecutar la consulta
    cursor.execute("SELECT nombre, fecha, cantidad FROM records")  # Ejecuta la consulta para obtener todos los registros
    results = cursor.fetchall()  # Obtiene los resultados
    cursor.close()  # Cierra el cursor
    conn.close()  # Cierra la conexión a la base de datos

    # Crea un DataFrame de pandas con los resultados obtenidos
    df = pd.DataFrame(results, columns=['nombre', 'fecha', 'cantidad'])
    df['fecha'] = pd.to_datetime(df['fecha'])  # Convierte la columna 'fecha' en formato datetime
    df['dia_semana'] = df['fecha'].dt.day_name()  # Añade una columna con el nombre del día de la semana

    dia_semana_actual = datetime.now().strftime("%A")  # Obtiene el nombre del día actual
    df_filtered = df[df['dia_semana'] == dia_semana_actual]  # Filtra los datos para el día de la semana actual

    # Agrupa por 'nombre' y calcula el promedio de la columna 'cantidad'
    promedio_por_empresa = df_filtered.groupby('nombre')['cantidad'].mean().reset_index()
    promedios = promedio_por_empresa.set_index('nombre')['cantidad'].to_dict()  # Convierte el resultado en un diccionario
    return promedios  # Retorna los promedios

# Verifica si el conteo diario está por debajo del 80% del promedio
def check_below_threshold(daily_count, average_count):
    threshold = average_count * 0.8  # Calcula el umbral como el 80% del promedio
    return daily_count < threshold  # Retorna True si el conteo está por debajo del umbral

# Notifica si el conteo diario está por debajo del umbral
def notify_if_below_threshold(daily_count, average_count, nombre):
    if check_below_threshold(daily_count, average_count):  # Verifica si está por debajo del umbral
        # Muestra un mensaje de advertencia
        messagebox.showwarning("Advertencia", f"{nombre} ha subido menos artículos de los esperados.")

# Carga datos de los últimos 7 días desde la base de datos y los organiza en una tabla
def load_data_from_db():
    try:
        # Conexión a la base de datos MySQL
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='0908',
            database='periodicos'
        )
        cursor = conn.cursor()  # Crea el cursor para ejecutar la consulta
        cursor.execute("SELECT nombre, fecha, cantidad FROM records")  # Ejecuta la consulta para obtener todos los registros
        results = cursor.fetchall()  # Obtiene los resultados

        data = {}  # Diccionario para almacenar los datos por empresa
        for nombre, fecha, cantidad in results:  # Itera sobre los resultados
            if nombre not in data:
                data[nombre] = [''] * 7  # Inicializa una lista de 7 elementos vacíos para cada empresa
            fecha_str = fecha.strftime("%Y-%m-%d")  # Convierte la fecha en cadena
            # Verifica si la fecha está entre los últimos 7 días
            index = get_last_7_days().index(fecha_str) if fecha_str in get_last_7_days() else -1
            if index >= 0:
                data[nombre][index] = cantidad  # Asigna la cantidad al día correspondiente

        # Inserta los datos en la tabla Treeview
        for nombre, cantidades in data.items():
            tree.insert("", "end", values=[nombre] + cantidades)

    except Exception as e:
        # Muestra un mensaje de error si ocurre una excepción
        messagebox.showerror("Error", f"No se pudieron cargar los datos:\n{e}")
    finally:
        if conn:
            conn.close()  # Cierra la conexión a la base de datos

# Obtiene una lista de fechas de los últimos 7 días
def get_last_7_days():
    today = datetime.now()  # Fecha actual
    return [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]  # Retorna una lista con las últimas 7 fechas

# Muestra la tabla con los datos de los últimos 7 días
def show_table():
    last_7_days = get_last_7_days()  # Obtiene los últimos 7 días
    columns = ['nombre'] + last_7_days  # Define las columnas de la tabla
    # Crea una tabla Treeview con las columnas correspondientes
    tree = ttk.Treeview(table_frame, columns=columns, show='headings')

    # Configura los encabezados y las columnas de la tabla
    for col in columns:
        tree.heading(col, text=col)  # Asigna el nombre a cada encabezado de columna
        tree.column(col, anchor="center")  # Centra el contenido de la columna

    tree.pack(expand=True, fill='both')  # Muestra la tabla en el frame
    return tree  # Retorna el objeto de la tabla



# Carga todos los datos de la base de datos y los organiza por nombre y fecha
def load_all_data_from_db():
    try:
        # Conexión a la base de datos MySQL
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='0908',
            database='periodicos'
        )
        cursor = conn.cursor()  # Crea el cursor para ejecutar la consulta
        cursor.execute("SELECT nombre, fecha, cantidad FROM records")  # Ejecuta la consulta para obtener los registros
        results = cursor.fetchall()  # Obtiene todos los resultados de la consulta

        data = {}  # Diccionario para almacenar los datos organizados por empresa y fecha
        fechas = set()  # Conjunto para almacenar las fechas únicas

        # Itera sobre los resultados y organiza los datos
        for nombre, fecha, cantidad in results:
            if nombre not in data:
                data[nombre] = {}  # Inicializa un diccionario vacío para cada empresa
            fecha_str = fecha.strftime("%Y-%m-%d")  # Convierte la fecha en cadena de texto
            data[nombre][fecha_str] = cantidad  # Asocia la cantidad a la fecha correspondiente
            fechas.add(fecha_str)  # Añade la fecha al conjunto de fechas

        fechas = sorted(fechas)  # Ordena las fechas en orden ascendente
        show_all_days_table(data, fechas)  # Muestra la tabla con todos los días registrados

    except Exception as e:
        # Muestra un mensaje de error si ocurre una excepción
        messagebox.showerror("Error", f"No se pudieron cargar los datos:\n{e}")
    finally:
        if conn:
            conn.close()  # Cierra la conexión a la base de datos

# Muestra una tabla con los datos de todas las fechas disponibles
def show_all_days_table(data, fechas):
    columns = ['nombre'] + fechas  # Define las columnas como el nombre y las fechas
    # Crea una tabla Treeview con las columnas correspondientes
    tree = ttk.Treeview(table_frame, columns=columns, show='headings')

    # Configura los encabezados y las columnas de la tabla
    for col in columns:
        tree.heading(col, text=col)  # Asigna el nombre a cada encabezado de columna
        tree.column(col, anchor="center")  # Centra el contenido de la columna

    # Inserta los datos en la tabla, mostrando el nombre y las cantidades por fecha
    for nombre, cantidades in data.items():
        values = [nombre] + [cantidades.get(fecha, '') for fecha in fechas]  # Obtiene las cantidades para cada fecha
        tree.insert("", "end", values=values)  # Inserta la fila en la tabla

    tree.pack(expand=True, fill='both')  # Muestra la tabla en el frame
    return tree  # Retorna el objeto de la tabla

# Añade un nuevo nombre a la tabla
def add_name():
    name = name_entry.get()  # Obtiene el nombre del campo de entrada
    if name:
        # Inserta una nueva fila en la tabla con el nombre y siete campos vacíos para las cantidades
        tree.insert("", "end", values=[name] + [''] * 7)

# Añade el número de artículos a la tabla para la fecha actual
def add_number():
    selected_item = tree.selection()  # Obtiene el elemento seleccionado en la tabla
    if selected_item:
        current_date = datetime.now().strftime("%Y-%m-%d")  # Obtiene la fecha actual en formato YYYY-MM-DD
        values = tree.item(selected_item)['values']  # Obtiene los valores de la fila seleccionada

        # Verifica si la fecha actual ya está en los valores de la fila seleccionada
        if current_date not in values:
            number = number_entry.get()  # Obtiene el número de artículos del campo de entrada
            if number.isdigit():  # Verifica si el número es válido
                current_index = get_last_7_days().index(current_date) + 1  # Obtiene el índice de la fecha actual
                values[current_index] = number  # Actualiza el valor en la fila
                tree.item(selected_item, values=values)  # Actualiza la fila en la tabla

                daily_count = int(number)  # Convierte el número de artículos en entero
                promedios = calculate_weekday_average()  # Calcula los promedios por empresa
                nombre = values[0]  # Obtiene el nombre de la empresa
                avg_count = promedios.get(nombre, 0)  # Obtiene el promedio de la empresa

                notify_if_below_threshold(daily_count, avg_count, nombre)  # Notifica si está por debajo del umbral
        else:
            # Muestra un mensaje de advertencia si se intenta modificar una fecha existente
            messagebox.showwarning("Advertencia", "No se puede modificar el valor de la fecha actual.")

# Carga un archivo CSV y sube los datos a la base de datos
def upload_file():
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])  # Abre un diálogo para seleccionar el archivo
    if file_path:
        try:
            df = pd.read_csv(file_path)  # Lee el archivo CSV en un DataFrame de pandas
            conn = mysql.connector.connect(
                host='localhost',
                user='root',
                password='0908',
                database='periodicos'
            )
            cursor = conn.cursor()  # Crea el cursor para ejecutar las consultas

            # Itera sobre las filas del DataFrame y sube los datos a la base de datos
            for index, row in df.iterrows():
                nombre = row['nombre']
                for date_col in row.index[1:]:
                    fecha = datetime.strptime(date_col, '%d-%m-%Y').date()  # Convierte la fecha en objeto date
                    cantidad = row[date_col]  # Obtiene la cantidad de artículos
                    cursor.execute("""
                        INSERT INTO records (nombre, fecha, cantidad)
                        VALUES (%s, %s, %s)
                    """, (nombre, fecha, cantidad))  # Inserta los datos en la base de datos

            conn.commit()  # Guarda los cambios en la base de datos
            messagebox.showinfo("Éxito", "Datos subidos correctamente.")  # Muestra un mensaje de éxito
            load_data_from_db()  # Carga los datos en la tabla
        except Exception as e:
            # Muestra un mensaje de error si ocurre una excepción
            messagebox.showerror("Error", f"No se pudo leer el archivo:\n{e}")
        finally:
            if conn:
                conn.close()  # Cierra la conexión a la base de datos

# Guarda los datos actuales de la tabla en la base de datos
def save_to_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='0908',
            database='periodicos'
        )
        cursor = conn.cursor()  # Crea el cursor para ejecutar las consultas

        # Itera sobre los elementos de la tabla y guarda los datos en la base de datos
        for child in tree.get_children():
            values = tree.item(child)['values']  # Obtiene los valores de la fila
            nombre = values[0]  # El primer valor es el nombre de la empresa
            fechas = values[1:]  # Los valores restantes son las cantidades

            # Itera sobre las fechas y cantidades para cada empresa
            for i, fecha in enumerate(get_last_7_days()):
                if fechas[i]:  # Solo guarda si hay una cantidad
                    cursor.execute("""
                        INSERT INTO records (nombre, fecha, cantidad)
                        VALUES (%s, %s, %s)
                    """, (nombre, fecha, fechas[i]))  # Inserta los datos en la base de datos

        conn.commit()  # Guarda los cambios en la base de datos
        messagebox.showinfo("Éxito", "Datos guardados en la base de datos.")  # Muestra un mensaje de éxito
    except Exception as e:
        # Muestra un mensaje de error si ocurre una excepción
        messagebox.showerror("Error", f"No se pudieron guardar los datos:\n{e}")
    finally:
        if conn:
            conn.close()  # Cierra la conexión a la base de datos



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


# Función para calcular la distribución de frecuencia
def calculate_frequency_distribution(data):
    """
    Calcula la distribución de frecuencia de la cantidad de artículos.
    """
    df = pd.DataFrame(data, columns=['fecha', 'cantidad'])
    df['fecha'] = pd.to_datetime(df['fecha'])
    # Extraer el día de la semana.
    df['dia_semana'] = df['fecha'].dt.day_name()
    # Contar la frecuencia de cada día de la semana.
    frequency_distribution = df['dia_semana'].value_counts().sort_index()
    return frequency_distribution


# Función para mostrar la distribución de frecuencia
def show_frequency_distribution():
    data = load_data()
    frequency_distribution = calculate_frequency_distribution(data)

    # Crear una ventana emergente para mostrar la tabla
    freq_window = tk.Toplevel(root)
    freq_window.title("Distribución de Frecuencia")
    freq_window.geometry("400x300")

    # Crear Treeview para mostrar la distribución
    columns = ['Día', 'Frecuencia']
    freq_tree = ttk.Treeview(freq_window, columns=columns, show='headings')

    for col in columns:
        freq_tree.heading(col, text=col)
        freq_tree.column(col, anchor="center")

    # Agregar los datos al Treeview
    for dia, frecuencia in frequency_distribution.items():
        freq_tree.insert("", "end", values=[dia, frecuencia])

    freq_tree.pack(expand=True, fill='both')


# Botón para mostrar la distribución de frecuencia
show_frequency_button = ttk.Button(button_frame, text="Mostrar Distribución de Frecuencia",
                                   command=show_frequency_distribution)
show_frequency_button.pack(side='left', padx=5, pady=5)

# Mostrar la tabla inicial
tree = show_table()

# Iniciar el bucle de la interfaz gráfica
root.mainloop()
