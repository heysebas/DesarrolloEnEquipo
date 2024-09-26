# database.py
import mysql.connector
from config import DB_CONFIG
from utils import get_last_6_months_data, get_last_7_days

def connect_db():
    return mysql.connector.connect(**DB_CONFIG)

def load_data():
    start_date, end_date = get_last_6_months_data()
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, cantidad FROM records WHERE fecha BETWEEN %s AND %s", (start_date, end_date))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def load_data_from_db(tree):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, fecha, cantidad FROM records")
        results = cursor.fetchall()

        data = {}
        for nombre, fecha, cantidad in results:
            if nombre not in data:
                data[nombre] = [''] * 7
            fecha_str = fecha.strftime("%Y-%m-%d")
            index = get_last_7_days().index(fecha_str) if fecha_str in get_last_7_days() else -1
            if index >= 0:
                data[nombre][index] = cantidad

        for nombre, cantidades in data.items():
            tree.insert("", "end", values=[nombre] + cantidades)

    except Exception as e:
        raise RuntimeError(f"No se pudieron cargar los datos: {e}")
    finally:
        if conn:
            conn.close()

def save_to_db(tree):
    try:
        conn = connect_db()
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
    except Exception as e:
        raise RuntimeError(f"No se pudieron guardar los datos: {e}")
    finally:
        if conn:
            conn.close()
