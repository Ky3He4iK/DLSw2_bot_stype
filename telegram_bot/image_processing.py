from telegram_bot.model import StyleTransferModel
from io import BytesIO

_model = StyleTransferModel()


def _get_images(bot, img_id, out):
    bot.download(img_id, out=out)


def _upload_img(bot, chat_id, output):
    output_stream = BytesIO()
    output.save(output_stream, format='PNG')
    output_stream.seek(0)
    bot.send_photo(chat_id, photo=output_stream)


def styling(bot, img_content_id, img_style_id, chat_id):
    """
    receive two images; transfer style from one to another and send output image to [chat_id]
    """
    # первая картинка, которая к нам пришла станет content image, а вторая style image
    print("Transfer style form {} to {} for {}".format(img_content_id, img_style_id, chat_id))
    content_image_stream = BytesIO()
    style_image_stream = BytesIO()

    _get_images(bot, img_content_id, content_image_stream)
    _get_images(bot, img_style_id, style_image_stream)

    output = _model.transfer_style(content_image_stream, style_image_stream)

    # теперь отправим назад фото
    _upload_img(bot, output, chat_id)
    print("Done!")


def get_default_styles():
    return []
    # ("name", "description", "image_id")
