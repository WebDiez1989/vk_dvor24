import os
import sqlite3
import sys

import config_dvor24

app_dir = sys.path[0] or os.path.dirname(os.path.realpath(sys.argv[0])) or os.getcwd()

conn = sqlite3.connect((os.path.join(app_dir, config_dvor24.base)), check_same_thread=False)
cursor = conn.cursor()
try:
    cursor.execute("CREATE TABLE users (id INTEGER NOT NULL UNIQUE, user_id INTEGER NOT NULL UNIQUE, first_name TEXT, nickname TEXT,last_name TEXT, domain TEXT, city TEXT, country TEXT, menu TEXT, address TEXT, apartment TEXT, phone_number TEXT, activation_phone TEXT, activation_code INTEGER, PRIMARY KEY (id))")
except: pass
try:
    cursor.execute("CREATE TABLE users_dvor24 (id INTEGER PRIMARY KEY NOT NULL UNIQUE, user_id INTEGER UNIQUE NOT NULL, login TEXT, address TEXT, apartment TEXT, phone_number TEXT)")
except: pass
try:
    cursor.execute("CREATE TABLE request (id INTEGER PRIMARY KEY NOT NULL UNIQUE, user_id INTEGER NOT NULL, address TEXT NOT NULL, message TEXT, phone_number TEXT NOT NULL)")
except: pass
