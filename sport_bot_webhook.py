#!/usr/bin/env python3
import os

import gspread
import telebot
from dotenv import load_dotenv
from flask import Flask, request
from oauth2client.service_account import ServiceAccountCredentials
from telebot import custom_filters, types

load_dotenv()

APPROVAL_USERS = os.getenv("APPROVAL_USERS").split()

BOT_KEY = os.getenv("TOKEN")

SECRET = os.getenv("SECRET")

FILENAME = os.getenv("FILENAME")

URL = os.getenv("URL")

url = URL + SECRET

CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(BOT_KEY, threaded=False)
bot.remove_webhook()
bot.set_webhook(url=url)

app = Flask(__name__)


@app.route('/' + SECRET, methods=['POST'])
def webhook():
    r = request.stream.read().decode('utf-8')
    update = telebot.types.Update.de_json(r)
    bot.process_new_updates([update])
    return 'ok', 200


scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/spreadsheets',
         'https://www.googleapis.com/auth/drive.file',
         'https://www.googleapis.com/auth/drive']

creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
client = gspread.authorize(creds)
sheet = client.open(FILENAME).sheet1


def approve_users(message):
    return message.from_user.username in APPROVAL_USERS


@bot.message_handler(chat_id=[int(CHAT_ID)], commands=["add"])
def admin_rep(message):
    user_input = message.text
    if len(user_input.split()) > 1:
        APPROVAL_USERS.extend(user_input.split()[1:])
        m_for_user = "Пользователь добавлен"
        bot.send_message(message.chat.id, m_for_user)


@bot.message_handler(chat_id=[int(CHAT_ID)], commands=["remove"])
def admin_rep(message):
    user_input = message.text
    if len(user_input.split()) > 1 and user_input.split()[1] in APPROVAL_USERS:
        APPROVAL_USERS.remove(user_input.split()[1])
        m_for_user = "Пользователь удален"
        bot.send_message(message.chat.id, m_for_user)
    else:
        m_for_user = "Пользователя нет в списке одобренных"
        bot.send_message(message.chat.id, m_for_user)


@bot.message_handler(func=approve_users, commands=["start"])
def start(message):
    m_for_user = "Введите фамилию участника"
    bot.send_message(message.chat.id, m_for_user)


@bot.message_handler(func=approve_users, content_types=["text"])
def handle_text(message):

    data = sheet.get_all_records()

    user_answer = message.text
    result = []

    key = list(data[0].keys())[0]

    for el in data:
        if user_answer in el[key]:
            tmp = ". ".join(f"{key}: {value}" for key, value in el.items())
            result.append(tmp)

    if result != []:

        for el in result:
            bot.send_message(message.chat.id, el)

    else:
        m_for_user = "По Вашему запросу информация не найдена"
        bot.send_message(message.chat.id, m_for_user)


@bot.message_handler(content_types=["text"])
def handle_text_closed(message):
    m_for_user = "Вам запрещено получать ответы от бота"
    bot.send_message(message.chat.id, m_for_user)


bot.add_custom_filter(custom_filters.ChatFilter())
