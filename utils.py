# utils.py
import numpy as np
from datetime import datetime, timedelta

def get_last_6_months_data():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    return start_date, end_date

def get_last_7_days():
    today = datetime.now()
    return [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

def calculate_average(data):
    return np.mean([x[1] for x in data])

def check_below_threshold(daily_count, average_count):
    threshold = average_count * 0.8
    return daily_count < threshold

def notify_if_below_threshold(daily_count, average_count, nombre, messagebox):
    if check_below_threshold(daily_count, average_count):
        messagebox.showwarning("Advertencia", f"{nombre} ha subido menos artículos de los esperados.")
