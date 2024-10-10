# gui_utils.py

from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta

import mysql
import pandas as pd
from db_utils import load_data, load_data_from_db, save_to_db
from data_analysis import calculate_average, notify_if_below_threshold
from main import tree


def get_last_7_days():
    today = datetime.now()
    return [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

def show_table(table_frame):
    last_7_days = get_last_7_days()
    columns = ['nombre'] + last_7_days
    tree = ttk.Treeview(table_frame, columns=columns, show='headings')

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor="center")

    tree.pack(expand=True, fill='both')
    return tree

def add_name(name_entry):
    name = name_entry.get()
    if name:
        tree.insert("", "end", values=[name] + [''] * 7)

def add_number(tree, number_entry):
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
            messagebox.showinfo
