# -*- coding: utf-8 -*-

import random
import re

import requests
import json
from requests.exceptions import HTTPError

import config_dvor24

api_kay = config_dvor24.api_kay_dvor24
login = config_dvor24.login_dvor24
password = config_dvor24.password_dvor24
ApiLogin = {'login': login, 'password': password}

api_site = 'https://api.dvor24.com/'
billing = '/billing/user-balance-history'
cameras = '/cameras'
users = "api/v2/users"
user = "api/users"
auth = 'api/v2/auth/login'
billing_update = "/billing/user-balance-update"
objects = "api/v2/objects"
kay = ['x-vsaas-api-key', 'x-vsaas-session', 'x-vsaas-system-api-key']
api_system_key = {kay[2]: api_kay}




def auth_dvor24():
    response = requests.post(api_site + auth, params=ApiLogin) #Логинимся
    result = json.loads(response.text)
    json_authToken = result['result']['authToken']
    json_apiKey = result['result']['apiKey']
    # api_headers = {kay[0]: json_apiKey, kay[1]: json_authToken}
    api_headers_kay = {kay[0]: json_apiKey, kay[1]: json_authToken, kay[2]: api_kay}
    return api_headers_kay


def sr_street_home(street: str, home: str):
    api_headers = auth_dvor24()
    api_objects_params = {'search': street}
    response_objects = requests.get(api_site + objects, headers=api_headers,
                                    params=api_objects_params)  # Получаем данные об объектах
    result = json.loads(response_objects.text)['result']['result']
    for data in result:
        sr_home = home in data['address']
        if sr_home == True:
            return True, data
        else:
            pass

def search_user(login:str = ""):
    api_users_params = {'search': login}
    api_headers = auth_dvor24()
    response_users = requests.get(api_site + users, headers=api_headers, params=api_users_params) #Получаем данные о юзерах
    result = json.loads(response_users.text)['result']['users']

    return result


def user_activation(number_object, number_apartment, phone_number):
    user_login_dvor24 = number_object + "_" + number_apartment
    result2 = search_user(user_login_dvor24)
    for user in result2:
        if user_login_dvor24 == user['login']:
            user_result = user
            break
    try:
        if user_result['phone'] == '' or user_result['phone'] == phone_number:  # Если пользователь не имеет номера телефона или номер телефона совпал
            # Добавляем номер телефона пользователю, включаем, устанавливаем сгенерированный пароль
            user_password = user_edit_phone_number(user_result['id'], phone_number)
            if user_password != False:
                return True, "Логин: " + str(user_result['login']) + "\nПароль: " + str(user_password)
            else:
                return False, "Произошла ошибка сервера. Повторите запрос позже."
        else:
            number_true = "N_" in number_apartment
            if number_true == True:
                return False, "Пользователь уже активирован и имеет другой номер телефона"
            else:
                return user_activation(number_object, "N_" + number_apartment, phone_number)
    except:
        return False, "Не нашли такую квартиру в доме"


#Проверка активированного номера на наличие его в базе сервиса
def check_activ_number(phone_number: str):
    try:
        result = search_user(phone_number)
        for user in result:
            if user['phone'] == phone_number:
                login = user['login']
        if login is not None:
            street = sr_street_home(login.split('_')[0] + "_" + login.split('_')[1], "")[1]['address']
            return True, login, street
    except:
        return False








def user_edit_phone_number(id: str, phone_number: str):
    randomPassword = random.randint(100000, 999999)
    api_user_params = {"password": randomPassword, "phone": phone_number, "enabled": True}
    api_headers = auth_dvor24()
    response_user = requests.post('https://api.dvor24.com/api/v2/users/' + str(id) + '/manage', headers=api_headers, params=api_user_params) #Получаем данные о юзерах
    result2 = json.loads(response_user.text)['success']
    if result2 == "true":
        return randomPassword
    else:
        return False

def user_check_number(phone_number: str):
    #Отправляем код с подтверждением, записываем в базу код в колоку activation code
    api_user_params = {"countryId": "1", "phone": phone_number}
    api_headers = auth_dvor24()
    response_user = requests.post('https://api.dvor24.com/api/users/activation', headers=api_headers, params=api_user_params) #Получаем данные о юзерах
    result2 = json.loads(response_user.text)
    if result2['success'] == "false":
        message = result2['error']['message']
        if message == 'This number is already in use':
            message = 'Этот номер уже используется.\nВозможные причины:\n1. У вас уже есть аккаунт по данному адресу.\n2. Вы уже создали аккаунт по другому адресу.\n Для восстановления доступа перейдите на сайт https://cloud.dvor24.com/access-recovery\nДля присоединения второго адреса к существующему аккаунту напишите в поддержку.'
        return False, message
    else:
        return True, result2['result']['code']

#Проверяем номер телефона пользователя

