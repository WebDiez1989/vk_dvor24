import json
import os, re, sys
import sqlite3
import create_db
import api_dvor24
import config_dvor24
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor



app_dir = sys.path[0] or os.path.dirname(os.path.realpath(sys.argv[0])) or os.getcwd()

conn = sqlite3.connect((os.path.join(app_dir, config_dvor24.base)), check_same_thread=False)
cursor = conn.cursor()

####Ссылки на приложения.

app_android = "https://play.google.com/store/apps/details?id=ru.droid.moidvor"
app_ios = "https://apps.apple.com/ru/app/мой-двор/id1545530137"
app_web = "https://cloud.dvor24.com"
app_name_web = "Перейти в личный кабинет"

####Переменные сообщений
menu_text = 'Выберите нужный пункт меню'
start_menu_text = 'Добро пожаловать! Выберите нужный пункт меню'
get_access = 'Получить доступ к видеонаблюдению'
add_house = 'Оставить заявку на подключение дома'
message_add = 'Написать нам'
cencel = 'Отмена'
sr_street = 'Напишите название улицы и дом, без квартиры.\nНапример: Ленина 46/1'
sr_apartment = 'Введите номер квартиры. Только цифры.'
add_street_apartament = 'Прислали адрес с номером квартиры'
check_code = 'Ждем кода подтверждения'
resend_code = 'Отправить код повторно'
revers = 'Вернуться в главное меню'
requests_number = 'Ждем номер для обратной связи'
add_message_requests = "Добавить сообщение для заявки"
send_no_message = 'Отправить без сообщения'
resend_user = "Ответ пользователю"




session = vk_api.VkApi(token=config_dvor24.token_vk)


def db_table_sr(*user_id):
    cursor.execute('SELECT * FROM users WHERE user_id = ? ',
                   (user_id))
    one_result = cursor.fetchone()
    conn.commit()
    return one_result

def db_requests(
        user_id: str,
        message: str = False
):
    if message == False:
        cursor.execute('INSERT INTO request (user_id, address, message, phone_number) '
                       'VALUES '
                       '(?, '
                       '(SELECT address FROM users WHERE user_id LIKE ?), '
                       '?, '
                       '(SELECT phone_number FROM users WHERE user_id LIKE ?)'
                       ')',
                       (user_id, user_id, message, user_id))
    else:
        cursor.execute("UPDATE request SET message = ? WHERE ROWID = (SELECT ROWID FROM request WHERE user_id = ? ORDER BY ROWID DESC LIMIT 1)", (message, user_id))
    conn.commit()

def db_requests_send():
    cursor.execute("SELECT * FROM request WHERE ROWID ORDER BY ROWID DESC LIMIT 1")
    data = cursor.fetchone()
    return data

def db_table_update(
        user_id: str,
        menu: str = None,
        address: str = None,
        apartment: str = None,
        phone_number: str = None,
        activation_phone: str = None,
        activation_code: str = None

):
    cursor.execute("UPDATE users SET "
                   "menu = NULLIF(COALESCE(?, menu), ''), "
                   "address = NULLIF(COALESCE(?, address), ''), "
                   "apartment = NULLIF(COALESCE(?, apartment), ''), "
                   "phone_number = NULLIF(COALESCE(?, phone_number), ''), "
                   "activation_phone = NULLIF(COALESCE(?, activation_phone), ''), "
                   "activation_code = NULLIF(COALESCE(?, activation_code), '') "
                   "WHERE user_id = ?",
                   (menu,
                    address,
                    apartment,
                    phone_number,
                    activation_phone,
                    activation_code,
                    user_id))

    conn.commit()


def db_table_user_dvor24(user_login_dvor24, user_id: str):
    cursor.execute('INSERT INTO users_dvor24 (user_id, login, address, apartment, phone_number) VALUES (?, ?, (SELECT address FROM users WHERE user_id LIKE ?), (SELECT apartment FROM users WHERE user_id LIKE ?), (SELECT activation_phone FROM users WHERE user_id LIKE ?))',
        (user_id, user_login_dvor24, user_id, user_id, user_id))
    conn.commit()

def start_menu(user_id):
    keyboard_add([get_access, add_house, message_add], user_id, menu_text, one_time=True)
    db_table_update(address="", menu="", apartment="", user_id=user_id)

def send_message(user_id, message, keyboard=None):
    user_id = user_id,
    post = {
        "user_id": user_id,
        "message": message,
        "random_id": 0
    }
    if keyboard is not None:
        post["keyboard"] = keyboard.get_keyboard()
    else:
        post = post
    session.method("messages.send", post)

def getHistory(user_id, offset):
    post = {
        "user_id": user_id,
        "count": 1,
        "offset": offset
    }
    return session.method("messages.getHistory", post)


def keyboard_add(button:str, user_id, message, buttonCollor: str=False, one_time=False):
    keyboard = VkKeyboard(one_time=one_time)
    if buttonCollor == False:
        buttonCollor = []
        for btnc in button:
            if btnc == "Да":
                buttonCollor.append(VkKeyboardColor.POSITIVE)
            elif btnc == "Нет" or btnc == cencel:
                buttonCollor.append(VkKeyboardColor.NEGATIVE)
            else:
                buttonCollor.append(VkKeyboardColor.PRIMARY)
    lenButton = len(button)
    if lenButton % 2 == 1:
        lenButton += 1
    for btn, btnc in zip(button, buttonCollor):
        if lenButton % 2 == 1 or lenButton < len(button): # первую нечетную кнопку сопровождаем с новой строки
            if btn == "Нет" or btn == "Да":
                pass
            else:
                keyboard.add_line()
        lenButton -= 1
        keyboard.add_button(btn, btnc)
    send_message(user_id, message, keyboard)

def user_device(online_app):
    code_app = (2274003, 3140623, 3682744, 3697615, 3502557, 0)
    name_app = ("Android", "IPhone", "IPad", "Windows desktop", "Windows phone", "web")
    name_link_app = ("Скачать приложение на Android", "Скачать приложение на IPhone", "Скачать приложение на IPad", app_name_web, app_name_web, app_name_web)
    link_app = (app_android, app_ios, app_ios, app_web, app_web, app_web)
    for code, name, link, link_name in zip(code_app, name_app, link_app, name_link_app):
        if code == online_app:
            return {"code": code, "link_name": link_name, "link": link}

def sr_id(user_id):
    user = session.method("users.get", {"user_ids": user_id, "fields": "domain, nickname, city, country, online"})
    us_id = user[0]['id']
    first_name = user[0]['first_name']
    last_name = user[0]['last_name']
    nickname = user[0]['nickname']
    domain = user[0]['domain']
    try:
        city = user[0]['city']['title']
        country = user[0]['country']['title']
    except:
        city = ""
        country = ""
    try:
        online_app = user[0]['online_app']
    except: online_app = 0
    app_device = user_device(online_app)
    try:
        cursor.execute('INSERT INTO users (user_id, first_name, last_name, nickname, domain, city, country) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (us_id, first_name, last_name, nickname, domain, city, country))
        conn.commit()
    except: pass
    return dict({'user_id': us_id, 'first_name': first_name, 'last_name': last_name, 'nickname': nickname, 'domain': domain, 'city': city, 'country': country, 'app_device': app_device})

def number_check(user_id, text):
    try:
        match = re.fullmatch(r'(\+?(8|7)[\-\s]?)?\(?9\d{2}\)?[\-\s]?\d{3}[\-\s]?\d{2}[\-\s]?\d{2}', text)
        phone_number = "+7" + match.group()[-10:]
        # Смотрим активированный номер у пользователя.
        # Если номер не совпадает, отдаем ошибку
        if db_phone_activ is not None and db_phone_activ != phone_number: #Если ячейка с номером не пустая и имеет другой номер
            return False, "Вы ранее активировали другой номер."
        # elif db_table_sr(user_id)[12] == phone_number:
        #     return False, "Номер уже активирован, Попробуйте восстановить доступ на сайте."
        else:
            if db_phone_activ is not None and db_phone_activ == phone_number:
                check_number = "n_activ", "Этот номер уже активирован вами"
            else:
                check_number = api_dvor24.user_check_number(phone_number)
            if check_number[0] == True:
                # Записываем код в базу и ждем ввода кода
                return True,  check_number[1], phone_number
            else:
                return False, check_number[1]
    except:
        return False, "Формат номера не поддерживается. Убедитесь что вводите правильный номер."

def n_check(user_id, text):
    n_check = number_check(user_id, text)

    if n_check[0] is False:
        send_message(user_id, n_check[1])
    if n_check[0] == "n_activ":
        #Запускаем запись аккаунта
        pass

    elif n_check[0] is True:
        # db_table_phone(n_check[2], event.user_id)
        # db_table_activation_code(n_check[1], event.user_id)
        # db_table_menu(check_code, event.user_id)
        db_table_update(phone_number=n_check[2], activation_code=n_check[1], menu=check_code, user_id=user_id)
        keyboard_add([resend_code, cencel], user_id, "Для проверки номера пришлите код из смс")


vk = VkLongPoll(session)
print("start")
for event in vk.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        text = event.text.lower()
        user_info = "https://vk.com/" + sr_id(user_id)['domain'] + "\n" + sr_id(user_id)['first_name'] + " " + \
                    sr_id(user_id)['last_name']
        db_user = db_table_sr(user_id)

        db_domain = db_user[5]
        db_menu = db_user[8]
        db_address = db_user[9]
        db_apartment = db_user[10]
        db_phone = db_user[11]
        db_phone_activ = db_user[12]
        db_code = db_user[13]
        if db_user is None:    # Вносим данные пользователя в базу, если существует - игнорируем.
            sr_id(user_id)
            keyboard_add([get_access, add_house, message_add], user_id, start_menu_text, one_time=True)
        elif text != cencel.lower() and (text == get_access.lower() or db_menu == get_access.lower()):


            if db_phone_activ is not None:
                check_activ = api_dvor24.check_activ_number(db_phone_activ)
                if check_activ != False:
                    keyboard_add([revers], user_id, "У Вас уже есть активированный аккаунт по адресу:\n" + check_activ[2] + "\nЛогин: " + check_activ[1] + "\nЕсли вы не помните пароль, запросите восстановление на сайте.")
                    continue
            # Просим написать название улицы, если человек уже в меню просим еще раз написать.
            if get_access.lower() == text:
                keyboard_add([cencel], user_id, sr_street)
                # db_table_apartment(None, event.user_id)
                # db_table_menu(get_access.lower(), event.user_id)
                db_table_update(apartment="", menu=get_access.lower(), user_id=user_id)

            if db_menu == get_access.lower() and text != get_access.lower() : #Если прислали не название меню, но находятся в меню
                if text == "да" and db_address is not None:
                    #Запрвшиваем квартиру
                    keyboard_add([cencel], user_id, sr_apartment)
                    # db_table_apartment(text, event.user_id)
                    db_table_update(apartment=text, user_id=user_id)
                elif text == "нет" and db_address is not None:
                    # Сбрасываем значения меню и адреса на null и отправляем юзера в главное меню
                    # db_table_address(None, event.user_id)
                    # db_table_menu(None, event.user_id)
                    db_table_update(address="", menu="", user_id=user_id)
                    keyboard_add([get_access, add_house, message_add], user_id, menu_text, one_time=True)
                elif db_address is not None and db_apartment is not None: #Если нам уже известен адрес.
                    #Получаем номер квартиры
                    try:
                        apartment = re.findall(r'\d+', text)[0]
                        if apartment is not None:
                            send_message(user_id, "Ищем квартиру: " + apartment)
                            #Ищем в базе двора дом и данные по дому.
                            data = api_dvor24.sr_street_home(db_address, "")[1]
                            text_result = "По адресу:\nгород " + data['citytitle'] + "\n" + data['address'] + "\nАбонентская плата составляет: " + str(data['montlypayment']) + " рублей в месяц."
                            text_result2 = "\n\nАктивируя учетную запись вы соглашаетесь с условиями указанными на сайте:\nhttps://двор86.рф\n\nДля завершения регистрации и получения пароля пришлите номер телефона, он будет привязан к учетной записи."
                            text_result3 = "\n\nАктивируя учетную запись вы соглашаетесь с условиями указанными на сайте:\nhttps://двор86.рф\n\nДля завершения регистрации и получения пароля пришлите последние 4 цифры ранее активированного номера телефона."
                            # db_table_apartment(apartment, event.user_id)
                            db_table_update(apartment=apartment, user_id=user_id)
                            if db_phone_activ is not None:
                                send_message(user_id, text_result + text_result3)
                                # db_table_menu(check_code, event.user_id)
                                # db_table_activation_code(db_phone_activ[-4:], event.user_id)
                                db_table_update(activation_code=db_phone_activ[-4:], menu=check_code, user_id=user_id)
                            else:
                                send_message(user_id, text_result + text_result2)
                                # db_table_menu(add_street_apartament, event.user_id)
                                db_table_update(menu=add_street_apartament, user_id=user_id)
                    except: send_message(user_id, "Вы прислали не номер квартиры")
                elif db_address is None or db_address is not None:
                    try:
                        street_hous = re.findall(r'(\w+).?(\d+).?(\d+)?', text)[-1]
                        if street_hous[2] != '':
                            hous = street_hous[1] + "/" + street_hous[2]
                        else:
                            hous = street_hous[1]
                        street = street_hous[0]
                        street = re.findall(r'\D+', street)[0]
                        send_message(user_id, "Ищем необходимый дом, подождите...")
                        result_street_home = api_dvor24.sr_street_home(street, hous)
                    except: result_street_home = None
                    if result_street_home is None or result_street_home[0] == False:
                        keyboard_add([cencel], user_id, "Дом не найден в нашей базе. Попробуйте еще раз!\nПришлите ТОЛЬКО улицу и дом. ")

                    elif result_street_home is not None and result_street_home[0] == True:
                        keyboard_add(["Да", "Нет"], user_id, "Дом найден в нашей базе:\n" + result_street_home[1]['address'] + "\nВсе верно?", one_time=True)
                        # db_table_address(result_street_home[1]['address'], event.user_id)
                        db_table_update(address=result_street_home[1]['address'], user_id=user_id)
        elif db_menu == add_street_apartament and text != cencel.lower():
            n_check(user_id, text)
        elif db_menu == check_code and text != cencel.lower():
            if text ==resend_code.lower():
                n_check(user_id, db_phone)
            elif int(text) == db_code:
                #Делаем запрос дома
                data = api_dvor24.sr_street_home(db_address, "")[1]
                # Прикрепляем номер квартиры,
                user_login_dvor24 = data['number'] + '_' + db_apartment
                # Переносим номер телефона в активированные
                # db_table_activation_phone(db_phone, event.user_id)
                db_table_update(activation_phone=db_phone, user_id=user_id)
                # Делаем запрос на пользователя.
                activation = api_dvor24.user_activation(data['number'], db_apartment, db_phone_activ)
                if activation[0] == True:
                    keyboard = VkKeyboard(one_time=False)
                    keyboard.add_openlink_button(sr_id(user_id)['app_device']['link_name'], sr_id(user_id)['app_device']['link'])
                    keyboard.add_line()
                    keyboard.add_button(revers, VkKeyboardColor.PRIMARY)
                    send_message(user_id, "Доступ для личного кабинета:\n" + activation[1] + "\n\nМожете войти на сайте и скачать приложение на телефон", keyboard)
                    try:
                        db_table_user_dvor24(activation[1], event.user_id)
                    except: pass
                    # db_table_menu(None, event.user_id)
                    db_table_update(menu="", user_id=user_id)
                else:
                    send_message(user_id, activation[1])
            else:
                send_message(user_id, "Код не верный, попробуйте еще раз")
        elif text == add_house.lower():
            db_table_update(menu=text, user_id=event.user_id)
            keyboard_add([cencel], user_id, "Благодарим за проявленный интерес к эффективному видеонаблюдению.\n\nПо какому адресу планируется подключение?")
        elif db_menu == add_house.lower() and text != cencel.lower():
            send_message(user_id, "Отлично! По какому номеру с вами связаться?")
            db_table_update(menu=requests_number, address=text, user_id=event.user_id)
        elif db_menu == requests_number and text != cencel.lower():
            db_table_update(phone_number=text, menu=add_message_requests, user_id=event.user_id)
            keyboard_add([send_no_message], user_id, "Записали и передали! С вами свяжутся по указанному номеру в самое ближайшее время!\n\nЕсли хотите заявку дополнить сообщением, то можете его написать прямо сейчас", [VkKeyboardColor.NEGATIVE])
            db_requests(user_id)
        elif (db_menu == add_message_requests or text == send_no_message.lower()) and text != cencel.lower():
            #Все присланные данные кидаем в заявку.

            send_message(user_id, "До связи!")
            db_requests(user_id, text)
            start_menu(user_id)
            request = db_requests_send()
            data = "\nАдрес:" + request[2] + "\nСообщение: " + request[3] + "\nТелефон: " + request[4]
            send_message(config_dvor24.admin_id, "Новая заявка на подключение дома\n" + user_info + "\n " + data)
        elif text == message_add.lower() and text != cencel.lower():
            send_message(config_dvor24.admin_id, str(user_id) + "Сообщение от пользователя: \n" + user_info + "\n\n" + "Новый чат")
            db_table_update(menu=message_add.lower(), user_id=user_id)
            send_message(user_id, "Связываемся с менеджером")
            db_table_update(menu=message_add.lower(), user_id=config_dvor24.admin_id)
        elif db_menu == message_add.lower() and text != cencel.lower():

            if str(user_id) != config_dvor24.admin_id:
                if text == 'Завершить чат'.lower():
                    send_message(user_id, "Вы завершили чат")
                    send_message(config_dvor24.admin_id, str(user_id) + " -  Пользователь завершил чат:\nhttps://vk.com/" + sr_id(user_id)['domain'] + "\n" + sr_id(user_id)['first_name'] + " " + sr_id(user_id)['last_name'])
                    start_menu(user_id)
                else:
                    send_message(config_dvor24.admin_id, str(user_id) + " -  Сообщение от пользователя:\nhttps://vk.com/" + sr_id(user_id)['domain'] + "\n" + sr_id(user_id)['first_name'] + " " + sr_id(user_id)['last_name'] + "\n\n" + event.text)
            else:
                try:
                    reply = event.raw[7]['reply']
                    conversation_message_id = re.findall(r'\d+', reply)
                    post = {
                        "peer_id": user_id,
                        "conversation_message_ids":conversation_message_id
                    }
                    chat_id_message = re.findall(r'\d+', session.method('messages.getByConversationMessageId', post)['items'][0]['text'])[0]
                    keyboard_add(['Завершить чат'], chat_id_message, "Сообщение от поддержки:\n\n" + event.text)
                    db_table_update(menu=message_add.lower(), user_id=chat_id_message)
                except: send_message(user_id, "Вы забыли выбрать сообщение для ответа.")


                
        #         #Разбираем пересылаемое сообщение
        # elif user_id == config_dvor24.admin_id and db_menu == resend_user:
        #     #разбираем сообщение и отправляем ответ через "ответить"
        #     print(event.platform)
        #     pass


        elif text == cencel.lower() or text is not None: #Если прислали отмена или другой текст находясь в главном меню
            start_menu(user_id)