import json
import sqlite3
from datetime import datetime, timedelta
from sqlite3 import Error



async def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect(path)
        print("Connection to SQLite DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")

    return connection
def time_check(date):
    today_date = datetime.now()
    date = datetime.strptime(date, "%d-%m-%Y %H:%M:%S")
    weekday = today_date.weekday()
    end_of_current_week = today_date - timedelta(days=weekday + 1)
    end_of_current_week = end_of_current_week.replace(hour=23, minute=59, second=59, microsecond=0)
    start_of_current_week = end_of_current_week - timedelta(days=6)
    start_of_current_week = start_of_current_week.replace(hour=0, minute=0, second=0, microsecond=0)
    if start_of_current_week <= date <= end_of_current_week:
        return True
    else:
        return False

async def control_system_departure():
    path = 'C:\\Users\\Dmitry\\Downloads\\db.sqlite3'
    connection = await create_connection(path)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Shipments')
    shipments = cursor.fetchall()
    articles = []
    validators = []
    for shipment in shipments:
        if time_check(shipment[2]):
            cursor.execute(f'SELECT * FROM Orders WHERE id={shipment[1]}')
            order = cursor.fetchall()
            article = order[0][3]
            if article not in validators:
                articles.append({
                    'article': f'{order[0][3]}',
                    'XS': 0,
                    'S': 0,
                    'M': 0,
                    'L': 0,
                })
            validators.append(article)

    for shipment in shipments:
        if time_check(shipment[2]):
            cursor.execute(f'SELECT * FROM Orders WHERE id={shipment[1]}')
            order = cursor.fetchall()
            article_value = order[0][3]
            for article in articles:
                if article['article'] == article_value:
                    article['XS'] += shipment[4]
                    article['S'] += shipment[5]
                    article['M'] += shipment[6]
                    article['L'] += shipment[7]
    return articles

def write_json(file_path, data, encoding='utf-8', ensure_ascii=False):
    try:
        with open(file_path, 'w', encoding=encoding) as file:
            return json.dump(data, file, indent=4, ensure_ascii=ensure_ascii)
    except FileNotFoundError:
        print(f"File '{file_path}' not found ")
        return None
    except Exception as e:
        print(f"Error writing file '{file_path}': {e}")
        return None

def read_json(file_path, encoding='utf-8'):
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File '{file_path}' not found ")
        return None
    except Exception as e:
        print(f"Error reading file '{file_path}': {e}")
        return None