import logging
import os
import re

from dotenv import load_dotenv
import random

import sqlalchemy
from sqlalchemy.orm import sessionmaker
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

from create_db import create_db
from models import Words, Users, UserWords

load_dotenv()

# Создание и заполнение БД
create_db()

# Открытие сессии
def init_db():
    DNS = os.getenv('DNS')
    engine = sqlalchemy.create_engine(DNS)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

# Список пользователей
def user_list():
    with init_db() as session:
        users = session.query(Users).all()
        users = [user.cid for user in users]
        session.close()
        return users

# Добавление нового пользователя в список
def add_users(user_id):
    with init_db() as session:
        session.add(Users(cid=user_id))
        session.commit()
        session.close()

# Получение слов
def get_words(user_id):
    with init_db() as session:
        words = session.query(UserWords.word, UserWords.translate).\
            join(Users, Users.id == UserWords.id_user).\
            where(Users.cid == user_id).all()
        all_words = session.query(Words.word, Words.translate).all()
        words_list = all_words + words
        result = random.sample(words_list, 4)
        session.close()
        return result

# Добавление нового слова в список слов пользователя
def add_user_word(user_id, word, translate):
    with init_db() as session:
        id_user = session.query(Users.id).filter(Users.cid == user_id)
        session.add(UserWords(word=word, translate=translate, id_user=id_user))
        session.commit()
        session.close()

# Подсчёт количества слов пользователя
def get_count_user_words(user_id):
    with init_db() as session:
        total_words = session.query(UserWords.word).\
            join(Users, Users.id == UserWords.id_user).\
            where(Users.cid == user_id).count()
        session.close()
        return total_words


# Получение списка слов добавленных пользователем
def get_user_added_words(user_id):
    with init_db() as session:
        total_words = session.query(UserWords.id, UserWords.word, UserWords.translate).\
            join(Users, Users.id == UserWords.id_user).\
            where(Users.cid == user_id).all()
        session.close()
        return total_words


# Удаление слова из списка слов пользователя
def delete_words(word_id, user_id):
    with init_db() as session:
        us_id = session.query(UserWords.id_user). \
            join(Users, Users.id == UserWords.id_user). \
            where(Users.cid == user_id)
        word = session.query(UserWords).\
            where(UserWords.id == word_id,\
                   UserWords.id_user == us_id).one()
        session.delete(word)
        session.commit()
        session.close()


print('Start telegram bot...')

state_storage = StateMemoryStorage()   # Инициализация хранилища состояний
token = os.getenv('TOKEN')
bot = TeleBot(token, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []
user_current_word = {}

# Принимает несколько строк и возвращает их, каждую с новой строки
def show_hint(*lines):
    return '\n'.join(lines)

# Соединяет пару слов, целевое и его перевод
def show_target(data):
    return f'{data['target_word']} -> {data['translate_word']}'


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово 🔙'
    NEXT = 'Дальше ⏭'


# Класс позв. созд. подклассы StateGroup и созд. в них перемен. кот. должны быть экз. класса State
class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    other_words = State()


# Возвращает текущий шаг польз-ю по заданному идентификатору(uid)
def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0

# Обработчик сообщений от пользователя
@bot.message_handler(commands=['words', 'start'])
def create_words(message):
    types.ReplyKeyboardRemove()
    cid = message.chat.id
    if cid not in known_users:
        known_users.append(cid)
        add_users(cid)
        userStep[cid] = 0
        bot.send_message(cid, """Привет 👋 Давай попрактикуемся в английском языке. Тренировки можешь проходить\
 в удобном для себя темпе.
 
 У тебя есть возможность использовать тренажёр, как конструктор, и собирать свою собственную базу для обучения.\
 Для этого воспрользуйся инструментами:
 
 добавить слово ➕,
 удалить слово 🔙.
 
 Ну что, начнём ⬇️Доступные команды: /start""")

    markup = types.ReplyKeyboardMarkup(row_width=2)  # Создание клавиатуры с двумя кнопками

    global buttons
    buttons = []
    word = get_words(cid)
    target_word = word[0][0]
    translate = word[0][1]
    target_word_btn = types.KeyboardButton(target_word) # Кнопка для target_word
    buttons.append(target_word_btn)
    others = (word[1][0], word[2][0], word[3][0]) #[word for word in get_word[1:]] # Берём из БД 3 оставшихся пары из выборки
    others_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(others_words_btns)
    random.shuffle(buttons)

    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)

    buttons.extend([next_btn, add_word_btn, delete_word_btn])
    markup.add(*buttons)

    greeting = f'Выбери перевод слова:\nRU - {translate}'
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others
    buttons.clear()


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_words(message):
    create_words(message)


# Добавление нового слова
@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    userStep[cid] = 1
    bot.send_message(cid, 'Введите слово на английском для добавления:')


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
def add_word_get_word(message):
    try:
        word = message.text.lower()
        if not re.match("^[a-zA-Z]+$", word):
            msg = bot.reply_to(
                message,
                "Некорректный ввод. Используйте только латиницу. "
                "Попробуйте снова:"
            )
            bot.register_next_step_handler(msg, add_word_get_word)
            return

        user_current_word[message.chat.id] = {'word': word}
        msg = bot.reply_to(message, "Введите перевод на русский:")
        bot.register_next_step_handler(msg, add_word_get_translation)

    except Exception as e:
        logging.exception(f"Ошибка в обработчике add_word_to_db: {e}")
        bot.send_message(
            message.chat.id, "Произошла ошибка. Попробуйте позже.")

def add_word_get_translation(message):
    try:
        translate = message.text.lower()
        if not re.match("^[а-яА-ЯёЁ]+$", translate):
            msg = bot.reply_to(
                message,
                "Некорректный ввод. Используйте только кириллицу. "
                "Попробуйте снова:"
            )
            bot.register_next_step_handler(msg, add_word_get_translation)
            return

        cid = message.chat.id
        word = user_current_word[cid]['word']
        add_user_word(cid, word, translate)
        total_words = get_count_user_words(cid)
        bot.send_message(cid, f'Слово добавлено. Всего добавлено слов: {total_words}.')
        userStep[cid] = 0
        create_words(message)

    except Exception as e:
        logging.exception(
            f"Ошибка в обработчике add_word_get_translation: {e}")
        bot.send_message(
            message.chat.id, "Произошла ошибка. Попробуйте позже.")


# Удаление слова
@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    cid = message.chat.id
    try:
        words = get_user_added_words(cid)

        if not words:
            bot.send_message(
                message.chat.id, "Нет доступных слов для удаления.")
            return

        markup = types.InlineKeyboardMarkup()
        for word_id, word, translation in words:
            button_text = f"{word} ({translation})"
            callback_data = f"delete_word_confirm:{word_id}"
            button = types.InlineKeyboardButton(
                text=button_text, callback_data=callback_data)
            markup.add(button)

        bot.send_message(
            message.chat.id, "Выберите слово для удаления:", reply_markup=markup)

    except Exception as e:
        logging.exception(f"Ошибка в обработчике delete_word: {e}")
        bot.send_message(
            message.chat.id, "Произошла ошибка. Попробуйте позже.")


@bot.callback_query_handler(func=lambda call: call.data.startswith('delete_word_confirm:'))
def delete_word_confirmation(call):
    cid = call.message.chat.id
    try:
        word_id = call.data.split(':')[1]
        user_id = cid

        delete_words(word_id, user_id)
        bot.send_message(cid, 'Слово удалено')
        create_words(call.message)

    except Exception as e:
        logging.exception(
            f"Ошибка в обработчике delete_word_confirmation: {e}")
        bot.send_message(
            call.message.chat.id, "Произошла ошибка. Попробуйте позже.")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ['Отлично!❤', hint]
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons.extend([next_btn, add_word_btn, delete_word_btn])
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint('Допущена ошибка!',
                             f'Попробуй ещё раз вспомнить слово RU - {data['translate_word']}')
        markup.add(*buttons)
        bot.send_message(message.chat.id, hint, reply_markup=markup)


bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)


