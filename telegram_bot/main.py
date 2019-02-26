import telegram_bot.image_processing as image_processing
import telegram_bot.bot_token as bot_token
from telegram_bot.config import Config

import datetime

from multiprocessing import Queue, Process
from time import sleep

from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler
import logging

# В бейзлайне пример того, как мы можем обрабатывать две картинки, пришедшие от пользователя.
# При реалиазации первого алгоритма это Вам не понадобится, так что можете убрать загрузку второй картинки.
# Если решите делать модель, переносящую любой стиль, то просто вернете код)
# Styling bot
users = dict()  # [count_today; last_file_id, last_state_id]
job_queue = Queue()
keep_going_on = True
_updater = None


def worker(bot, queue):
    canceled_day = -1
    while keep_going_on:
        # today nobody was sent photos
        now = datetime.datetime.now()
        if now.hour == 0 and now.day != canceled_day:
            canceled_day = now.day
            for key, val in users:
                if val[1] is None and val[2] == -1:  # clean db
                    del users[key]
                else:
                    users[key] = [0, *val[1:]]

        if not queue.empty():
            # Получаем сообщение с картинкой из очереди и обрабатываем ее
            try:
                chat_id, img_content, img_style = queue.get()
                image_processing.styling(bot, img_content, img_style, chat_id)
            except BaseException as e:
                print(e, e.__cause__, e.args)
        sleep(3)
    print("Stopping. Processing last photos from queue")
    while not queue.empty():
        # Получаем сообщение с картинкой из очереди и обрабатываем ее
        chat_id, img_content, img_style = queue.get()
        image_processing.styling(bot, img_content, img_style, chat_id)


def send_prediction_on_photo(_, update):
    # Нам нужно получить две картинки, чтобы произвести перенос стиля, но каждая картинка приходит в
    # отдельном апдейте, поэтому в простейшем случае мы будем сохранять id первой картинки в память,
    # чтобы, когда уже придет вторая, мы могли загрузить в память уже сами картинки и обработать их.
    chat_id = update.message.chat_id
    if chat_id in users and users[chat_id][0] > Config.TRANSFERRING_PER_DAY:
        update.message.reply_text("Прости, я не могу обработать так много фотографий за день. Приходи завтра")
        print("Too many requests from {}".format(chat_id))
        return
    print("Got image from {}".format(chat_id))

    # получаем информацию о картинке
    # image = None
    # for img in update.message.photo[::-1]:
    #     if img.height * img.width <= 3000000:
    #         image = img
    #         break

    # image_file = bot.get_file(image)
    image_id = update.message.photo[-1].file_id

    if chat_id in users and users[chat_id][1]:
        # (chat_id, ing_content, img_style)
        if users[chat_id][2] == 2:
            job_queue.put((chat_id, image_id, users[chat_id][1]))
        else:
            job_queue.put((chat_id, users[chat_id][1], image_id))
        users[chat_id] = [users[chat_id][0] + 1, None, -1]
        # image_processing.styling(bot, first_image_file[chat_id], image_id, chat_id)
        update.message.reply_text("В скором времени я всё обработаю и пришлю тебе результат")
    else:
        users[chat_id] = [0, image_id, -1]
        button_list = [
            [InlineKeyboardButton("Изменить стиль", callback_data="|".join((image_id, "1")))],
            [InlineKeyboardButton("Источник стиля", callback_data="|".join((image_id, "2")))]
        ]
        reply_markup = InlineKeyboardMarkup(button_list)
        # bot.send_message(..., "A two-column menu", reply_markup=reply_markup)
        update.message.reply_text("что хочешь сделать с этой фотографией?", reply_markup=reply_markup)


def cmd_handler(_, update):
    if update.message.text == '/start' or update.message.text == '/help':
        update.message.reply_text(Config.HELP_MSG)
    if update.message.text == '/ping':
        update.message.reply_text("Pong!")
    pass


def handle_inline_kb(bot, update):
    # chat_id, kb_content
    chat_id = update.callback_query.message.chat_id
    file_id, mode = update.callback_query.data.split('|')
    count = users[chat_id][0] if chat_id in users else 0
    if mode == "1":
        # todo: predefined styles
        users[chat_id] = [count, file_id, 1]
        bot.send_message(chat_id=chat_id,
                         text="Хорошо, теперь загрузи изображения, в стиле которого ты хочешь фотографию")
    elif mode == "2":
        users[chat_id] = [count, file_id, 2]
        bot.send_message(chat_id=chat_id, text="Хорошо, теперь загрузи изображения, которое ты хочешь стилизовать")


def stop():
    global keep_going_on
    keep_going_on = False
    _updater.stop()
    sleep(600)
    exit(0)
    # todo: adequate stopping


def main():
    # Включим самый базовый логгинг, чтобы видеть сообщения об ошибках
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)

    global _updater

    _updater = Updater(token=bot_token.token)

    worker_args = (_updater.bot, job_queue)
    worker_process = Process(target=worker, args=worker_args)
    worker_process.start()

    # В реализации большого бота скорее всего будет удобнее использовать Conversation Handler
    # вместо назначения handler'ов таким способом
    _updater.dispatcher.add_handler(MessageHandler(Filters.photo, send_prediction_on_photo))
    _updater.dispatcher.add_handler(MessageHandler(Filters.command, cmd_handler))
    _updater.dispatcher.add_handler(CallbackQueryHandler(handle_inline_kb))

    print("To stop me just send `Stop` to localhost:4717")
    _updater.start_polling()


if __name__ == '__main__':
    main()
