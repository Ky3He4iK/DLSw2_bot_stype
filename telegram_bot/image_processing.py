from telegram_bot.model import StyleTransferModel
from telegram_bot.config import Config

from io import BytesIO
import time
from PIL import Image

_model = StyleTransferModel()


def _get_image(bot, img_id):
    byte_stream = BytesIO()
    bot.get_file(img_id).download(out=byte_stream)
    img = Image.open(byte_stream)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    return img.resize(Config.IMAGE_SIZE, Image.ANTIALIAS), img.size


def _upload_img(bot, chat_id, output):
    output_stream = BytesIO()
    output.save(output_stream, format='PNG')
    output_stream.seek(0)
    msg = bot.send_photo(chat_id=chat_id, photo=output_stream)
    return msg.photo[-1].file_id


def styling(bot, img_content_id, img_style_id, chat_id):
    """
    receive two images; transfer style from one to another and send output image to [chat_id]
    """
    # первая картинка, которая к нам пришла станет content image, а вторая style image
    print("Transfer style form {} to {} for {}".format(img_content_id, img_style_id, chat_id))
    start_time = time.time()

    content, content_size = _get_image(bot, img_content_id)
    style, _ = _get_image(bot, img_style_id)

    output = _model.transfer_style(content, style)

    # теперь отправим назад фото
    img_id = _upload_img(bot, chat_id, output.resize(content_size, Image.ANTIALIAS))
    print("Done! Image id: {}\ntime taken: {} s".format(img_id, int(time.time() - start_time)))


def get_default_styles():
    return []
    # ("name", "description", "image_id")
