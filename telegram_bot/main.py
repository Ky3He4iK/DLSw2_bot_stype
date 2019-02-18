from telegram_bot.model import StyleTransferModel
import telegram_bot.listener
import telegram_bot.image_processing as image_processing
import telegram_bot.bot_token as bot_token
from telegram_bot.config import Config

from io import BytesIO
import datetime

from multiprocessing import Queue, Process
from time import sleep

from telegram.ext import Updater, MessageHandler, Filters
import logging

# В бейзлайне пример того, как мы можем обрабатывать две картинки, пришедшие от пользователя.
# При реалиазации первого алгоритма это Вам не понадобится, так что можете убрать загрузку второй картинки.
# Если решите делать модель, переносящую любой стиль, то просто вернете код)
# Styling bot
model = StyleTransferModel()
users = dict()  # [count_today; last_file_id, last_state_id]
job_queue = Queue()
keep_going_on = True


def upload_res(bot, chat_id, output):
    output_stream = BytesIO()
    output.save(output_stream, format='PNG')
    output_stream.seek(0)
    bot.send_photo(chat_id, photo=output_stream)


def worker(bot, queue):
    canceled_day = -1
    while keep_going_on:
        now = datetime.datetime.now()
        if now.hour == 0 and now.day != canceled_day:
            canceled_day = now.day
            for key, val in users:
                users[key] = [0, *val[1:]]
        if not queue.empty():
            # Получаем сообщение с картинкой из очереди и обрабатываем ее
            chat_id, img_content, img_style = queue.get()
            image_processing.styling(bot, img_content, img_style, chat_id)
        sleep(1)


def photo(_, update):
    update.message.reply_text("Ваше фото помещено в очередь")
    job_queue.put(update.message)


def send_prediction_on_photo(_, update):
    # Нам нужно получить две картинки, чтобы произвести перенос стиля, но каждая картинка приходит в
    # отдельном апдейте, поэтому в простейшем случае мы будем сохранять id первой картинки в память,
    # чтобы, когда уже придет вторая, мы могли загрузить в память уже сами картинки и обработать их.
    chat_id = update.message.chat_id
    print("Got image from {}".format(chat_id))

    # получаем информацию о картинке
    image = None
    for img in update.message.photo[::-1]:
        if img.height * img.width <= 3000000:
            image = img
            break
    # image_file = bot.get_file(image)
    image_id = image.file_id

    if chat_id in users:
        if users[chat_id][1] is None:
            users[chat_id][1] = image_id
        else:
            # (chat_id, ing_content, img_style)
            job_queue.put((chat_id, users[chat_id][1], image_id))
            users[chat_id][1] = None
            # image_processing.styling(bot, first_image_file[chat_id], image_id, chat_id)
    else:
        users[chat_id] = [chat_id, image_id,  -1]


def just_text(_, update):
    if update.message.text == '/start' or update.message.text == '/help':
        update.reply_text(Config.HELP_MSG)
    if update.message.text == '/ping':
        update.reply_text("Pong!")
    pass


def stop():
    global keep_going_on
    keep_going_on = False
    sleep(60)
    exit(0)
    # todo: adequate stopping


def main():
    # Включим самый базовый логгинг, чтобы видеть сообщения об ошибках
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
    updater = Updater(token=bot_token.token)

    worker_args = (updater.bot, job_queue)
    worker_process = Process(target=worker, args=worker_args)
    worker_process.start()

    # В реализации большого бота скорее всего будет удобнее использовать Conversation Handler
    # вместо назначения handler'ов таким способом
    updater.dispatcher.add_handler(MessageHandler(Filters.photo, send_prediction_on_photo))
    updater.dispatcher.add_handler(MessageHandler(Filters.command, just_text))
    updater.start_polling()


if __name__ == '__main__':
    main()
