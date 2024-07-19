import os
import requests
import dotenv
import json
from datetime import datetime, timedelta

def request_to_api_modulbank(start_date_month):
    dotenv.load_dotenv()
    token_modulbank = os.getenv('TOKEN')
    url_payments_income = os.getenv('URLPAY')
    headers_modulbank = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token_modulbank}"
    }
    params_modulbank = {
        "from": f"{start_date_month}",
        "records": 50
    }

    res_pay = requests.post(url_payments_income, headers=headers_modulbank, json=params_modulbank)
    return res_pay

