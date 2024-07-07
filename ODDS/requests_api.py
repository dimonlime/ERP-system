import os
import requests
import dotenv
import json
from datetime import datetime, timedelta

dotenv.load_dotenv()

token_modulbank = os.getenv('TOKEN')
url_payments_income = os.getenv('URLPAY')

headers_modulbank = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token_modulbank}"
}

params_modulbank = {
    "from": f"2024-06-01",
    "records": 50
}

res_pay = requests.post(url_payments_income, headers=headers_modulbank, json=params_modulbank)

print(json.dumps(res_pay.json(), indent=4, ensure_ascii=False))