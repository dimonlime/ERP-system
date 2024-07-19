import asyncio
import json
import re
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import session, Session, sessionmaker
from sqlalchemy.future import select
from dateutil.parser import parse as parse_date
from database import PaymentsPurpose, Payment, IncomePurpose, Income, engine_ODDS, async_session_ODDS
from ODDS.requests_api import request_to_api_modulbank
from loguru import logger

def is_date_in_current_month(current_date, date_to_check):
    return current_date.year == date_to_check.year and current_date.month == date_to_check.month

def get_start_and_end_of_current_month(current_date):
    start_of_month = current_date.replace(day=1)
    if current_date.month == 12:
        end_of_month = current_date.replace(year=current_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_of_month = current_date.replace(month=current_date.month + 1, day=1) - timedelta(days=1)
    return start_of_month, end_of_month

async def parse_payments(response_pay, session):
    payments_list = []
    date_now = datetime.now()
    async with session as sess:
        result = await sess.execute(select(PaymentsPurpose))
        payments_purpose = result.scalars().all()

    for item in response_pay:
        payment_purpose = item['paymentPurpose']
        for payment in payments_purpose:
            code = f"{payment.code}"
            pattern = fr'\b{re.escape(code)}\b'
            print(pattern)
            if re.search(pattern, payment_purpose):
                date = item['created']
                amount = item['amount']
                date_obj = parse_date(date)
                if is_date_in_current_month(date_now, date_obj):
                    payments_list.append({'code': payment.code, 'name': payment.name, 'amount': amount, 'date': date})
    print(payments_list)
    return payments_list

async def total_received(incomes, session):
    total_received_income = []
    total_received_wb = 0
    total_received_other = 0
    date_now = datetime.now().date()
    start_date, end_date = get_start_and_end_of_current_month(date_now)
    async with session as sess:
        result = await sess.execute(select(IncomePurpose))
        incomes_purpose = result.scalars().all()

    for item in incomes:
        for income_purpose in incomes_purpose:
            if (item['code'] == income_purpose.code) and (f"{income_purpose.code}" == '4111'):
                total_received_wb += item['amount']
            elif (item['code'] == income_purpose.code) and (f"{income_purpose.code}" == '4119'):
                total_received_other += item['amount']
    total_received_income.append({'code': 4111, 'name': 'от продажи продукции,товаров,услуг По Основному ОКВЭД', 'amount': total_received_wb, 'date': f"{start_date} - {end_date}"})
    total_received_income.append({'code': 4119, 'name': 'прочие поступления', 'amount': total_received_other, 'date': f"{start_date} - {end_date}"})

    return total_received_income

async def total_executed_payments(payments):
    total_executed_payments = []
    amount_supplier_for_material = 0
    amount_supplier_ff = 0
    amount_supplier_fabric = 0
    amount_supplier_other = 0
    amount_employess_paid = 0
    amount_credits = 0
    amount_taxes = 0
    amount_other_payments = 0
    date_now = datetime.now().date()
    start_date, end_date = get_start_and_end_of_current_month(date_now)
    for item in payments:
        if item['code'] == '4121':
            amount_supplier_for_material += item['amount']
        elif item['code'] == '41211':
            amount_supplier_ff += item['amount']
        elif item['code'] == '41212':
            amount_supplier_fabric += item['amount']
        elif item['code'] == '41213':
            amount_supplier_other += item['amount']
        elif item['code'] == '4122':
            amount_employess_paid += item['amount']
        elif item['code'] == '4123':
            amount_credits += item['amount']
        elif item['code'] == '4128':
            amount_taxes += item['amount']
        elif item['code'] == '4129':
            amount_other_payments += item['amount']
    total_executed_payments.append({'code': 4121, 'name': 'поставщикам за сырье, материалы, работы услуги - всего', 'amount': amount_supplier_for_material, 'date': f"{start_date} - {end_date}"})
    total_executed_payments.append({'code': 41211, 'name': 'поставщику ФФ', 'amount': amount_supplier_ff, 'date': f"{start_date} - {end_date}"})
    total_executed_payments.append({'code': 41213, 'name': 'Прочие подрядчики', 'amount': amount_supplier_other, 'date': f"{start_date} - {end_date}"})
    total_executed_payments.append({'code': 4122, 'name': 'в связи с оплатой труда работников', 'amount': amount_employess_paid, 'date': f"{start_date} - {end_date}"})
    total_executed_payments.append({'code': 4123, 'name': 'в связи с оплатой кредитных обязательств (тело кредита + проценты)', 'amount': amount_credits, 'date': f"{start_date} - {end_date}"})
    total_executed_payments.append({'code': 4128, 'name': 'иных налогов и сборов', 'amount': amount_taxes, 'date': f"{start_date} - {end_date}"})
    total_executed_payments.append({'code': 4129, 'name': 'прочие платежи', 'amount': amount_other_payments, 'date': f"{start_date} - {end_date}"})
    return total_executed_payments

async def full_amount_payments(payments, session):
    full_amount = []
    total_amount = 0
    date_now = datetime.now().date()
    start_date, end_date = get_start_and_end_of_current_month(date_now)
    async with session as sess:
        result = await sess.execute(select(PaymentsPurpose).filter_by(code=4120))
        full = result.scalar()

    for payment in payments:
        total_amount += payment['amount']
    full_amount.append({'code': full.code, 'name': full.name, 'amount': total_amount, 'date': f"{start_date} - {end_date}"})
    return full_amount

async def full_amount_incomes(incomes, session):
    full_amount = []
    total_amount = 0
    date_now = datetime.now().date()
    start_date, end_date = get_start_and_end_of_current_month(date_now)
    async with session as sess:
        result = await sess.execute(select(IncomePurpose).filter_by(code=4110))
        full = result.scalar()

    for income in incomes:
        total_amount += income['amount']
    full_amount.append({'code': full.code, 'name': full.name, 'amount': total_amount, 'date': f"{start_date} - {end_date}"})
    return full_amount

async def cash_flow_balance(full_payment, full_income, session):
    cash_flow_balance = []
    total_cash_flow = full_income[0]['amount'] - full_payment[0]['amount']
    date_now = datetime.now().date()
    start_date, end_date = get_start_and_end_of_current_month(date_now)
    async with session as sess:
        result = await sess.execute(select(IncomePurpose).filter_by(code=4100))
        cash_flow = result.scalar()

    cash_flow_balance.append({'code': cash_flow.code, 'name': cash_flow.name, 'amount': total_cash_flow, 'date': f"{start_date} - {end_date}"})
    return cash_flow_balance

async def parse_incomes(responsePay, session):
    incomes = []
    date_now = datetime.now()
    async with session as sess:
        result = await sess.execute(select(IncomePurpose))
        incomes_purpose = result.scalars().all()

    for item in responsePay:
        contragent_name = item['contragentName']
        status = item['status']
        for income_purpose in incomes_purpose:
            code = f"{income_purpose.code}"
            amount = item['amount']
            date = item['created']
            purpose = income_purpose.name
            date_object = parse_date(date)

            if is_date_in_current_month(date_now, date_object):
                if (('Вайлдберриз' in contragent_name) or ('ВАЙЛДБЕРРИЗ' in contragent_name)) and (status == "Received") and code == '4111':
                    incomes.append({'code': income_purpose.code, 'name': purpose, 'amount': amount, 'date': date})
                elif (('Вайлдберриз' not in contragent_name) and ('ВАЙЛДБЕРРИЗ' not in contragent_name)) and status == "Received" and code == '4119':
                    incomes.append({'code': income_purpose.code, 'name': purpose, 'amount': amount, 'date': date})

    return incomes

async def add_to_db_payments_incomes(records, model_class, session):
    async with session as sess:
        for record in records:
            existing_record = await sess.execute(select(model_class).filter_by(
                code=record['code'],
                date=record['date'],
                name=record['name'],
            ))
            existing_record = existing_record.scalar()

            if existing_record:
                existing_record.amount = record['amount']
            else:
                new_record = model_class(**record)
                sess.add(new_record)

        await sess.commit()

async def initial():
    logger.info("Парс апи модульбанка")
    date_now = datetime.now().date()
    start_date, end_date = get_start_and_end_of_current_month(date_now)
    response = request_to_api_modulbank(start_date)
    responsePay = response.json()
    async with async_session_ODDS() as session:
        parsed_payments = await parse_payments(responsePay, session)
        parsed_incomes = await parse_incomes(responsePay, session)
        full_payment = await full_amount_payments(parsed_payments, session)
        full_income = await full_amount_incomes(parsed_incomes, session)
        total_received_income = await total_received(parsed_incomes, session)
        total_executed_pay = await total_executed_payments(parsed_payments)
        full_cash_flow_balance = await cash_flow_balance(full_payment, full_income, session)

        await add_to_db_payments_incomes(full_payment, Payment, session)
        await add_to_db_payments_incomes(total_executed_pay, Payment, session)
        await add_to_db_payments_incomes(full_cash_flow_balance, Payment, session)

        await add_to_db_payments_incomes(full_income, Income, session)
        await add_to_db_payments_incomes(total_received_income, Income, session)

