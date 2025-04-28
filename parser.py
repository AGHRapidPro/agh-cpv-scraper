#!/usr/bin/python3

from bs4 import BeautifulSoup
import re
import requests
import urllib.request
import json
import pandas as pd
import os
import datetime

def fix_broken_file(df, file_name):

    reduced_df = df.iloc[:, :5]
    row_length = reduced_df.apply(lambda row: row.count(), axis=1)
    fixed_df = reduced_df[row_length == 5]
    fixed_df.to_excel(file_name + '.xlsx', index=False)
    print('fixed xls file')
    
def json_to_csv(file, file_name): 
    try:
        with open(file, encoding='utf-8') as input_file:
            df = pd.read_json(input_file)
        df.to_csv(file_name + '.csv', encoding='utf-8', index=False)
        print('csv file created')
    except ValueError:
        print('error while creating csv')


def month_to_number(month):
    return {
        'styczeń': 1,
        'luty': 2,
        'marzec': 3,
        'kwiecień': 4,
        'maj': 5,
        'czerwiec': 6,
        'lipiec': 7,
        'sierpień': 8,
        'wrzesień': 9,
        'październik': 10,
        'listopad': 11,
        'grudzień': 12
    }[month]

def safe_round(x):
    try:
        return str(round(float(x), 2))
    except ValueError:
        return '0'

def parse_order_list(file_name, output):
    df = pd.DataFrame(pd.read_excel(file_name))

    df.columns.values[0] = "lp"
    df.columns.values[1] = "code"
    df.columns.values[2] = "name"
    df.columns.values[3] = "price_pln"
    df.columns.values[4] = "price_eur"

    df_filtered = df[df['name'].notnull()]

    df_filtered = df_filtered.copy()
    df_filtered['price_pln'] = df_filtered['price_pln'].fillna(0).apply(lambda x: safe_round(x))

    df_filtered = df_filtered.copy()
    df_filtered['price_eur'] = df_filtered['price_eur'].fillna(0).apply(lambda x: safe_round(x))

    df_filtered = df_filtered.copy()
    df_filtered['code'] = df_filtered['code'].fillna('')

    product_dict = df_filtered.to_dict('records')

    result_dict = []

    temp_arr = []
    for item in product_dict:
        if item['price_pln'] == '0.0' and item['price_eur'] == '0.0' and len(temp_arr) > 0:
            result_dict.append({
                "category": temp_arr[0]['name'],
                "list": temp_arr
            })
            temp_arr = []
            temp_arr.append(item)
        else:
            temp_arr.append(item)


    try:
        with open(output + '.json', 'w', encoding='utf-8') as file:
            json.dump(result_dict, file, ensure_ascii=False)
        print("File written successfully!")
    except Exception as e:
        print(f"Error writing to file: {e}")

    return product_dict

def parse_xls_file(url, directory = 'C:/Users/Public/Documents'):
    headers = {"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'}
    page = requests.get(url, headers)
    soup = BeautifulSoup(page.text, "html.parser")

    links = soup.find_all('a', href = True)

    current_year = datetime.date.today().year
    current_month = datetime.date.today().month
    if(current_month < 10):
        current_month = '0' + str(current_month)

    folder = 'cpv'

    try:
        os.mkdir(directory + '/' + folder)
        print(f"Directory '{folder}' created successfully.")
    except FileExistsError:
        print(f"Directory '{folder}' already exists.")
    except PermissionError:
        print(f"Permission denied: Unable to create '{folder}'.")
    except Exception as exept:
        print(f"An error occurred: {exept}")

    directory = directory + '/' + folder

    for link in links:
        filename = link.get_text().strip()

        if(re.search(r'Dostawy i usługi .*plan zamówień publicznych \d{4} .*(grudzień( \d{1}\.?0?)?|listopad( \d{1}\.?0?)?|październik( \d{1}\.?0?)?|wrzesień( \d{1}\.?0?)?|sierpień( \d{1}\.?0?)?|lipiec( \d{1}\.?0?)?|czerwiec( \d{1}\.?0?)?|styczeń( \d{1}\.?0?)?|luty( \d{1}\.?0?)?|marzec( \d{1}\.?0?)?|kwiecień( \d{1}\.?0?)?|maj( \d{1}\.?0?)?)', filename, re.IGNORECASE)):
            file_year = re.search(r'20\d{2}', filename).group()
            file_month = re.search('grudzień|listopad|październik|wrzesień|sierpień|lipiec|czerwiec|styczeń|luty|marzec|kwiecień|maj', filename, re.IGNORECASE).group()
            file_month = month_to_number(file_month)
            if(file_month < 10):
                file_month = '0' + str(file_month)

            href = 'https://www.dzp.agh.edu.pl' + link.get('href')


            if(str(file_year) == str(current_year) and str(file_month) == str(current_month)):
                name = 'latest'
                output_name = directory + '/' + name 
            else:
                name = str(file_year) + '-' + str(file_month)
                output_name = directory + '/' + name            

            xls_name = output_name + '.xls'
            
            print(f'downloading {href} as {name}.xls')
            urllib.request.urlretrieve(href, xls_name)
            print('downloaded')

            df = pd.DataFrame(pd.read_excel(xls_name))
            if(len(df.columns) > 5):
                os.remove(xls_name)
                fix_broken_file(df, output_name)
                xls_name = xls_name + 'x'
                
            parse_order_list(xls_name, output_name)
            json_to_csv(output_name + '.json', output_name)

            os.remove(xls_name)
            os.remove(output_name + '.json')
            print('xls and json file deleted')

url = 'https://www.dzp.agh.edu.pl/dla-jednostek-agh/plany-zamowien-publicznych-agh/'

path = input('Set target path: ')

parse_xls_file(url, path)

