from model import StyleTransferModel
from config import Config

import time
from PIL import Image
import sys


_model = StyleTransferModel()


def fix_img(img):
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    return img.resize(Config.IMAGE_SIZE, Image.ANTIALIAS)


def main():
    _, content, style = sys.argv
    content_img = Image.open(content)
    content_size = content_img.size
    content_img = fix_img(content_img)

    style_img = fix_img(Image.open(style))
    start_time = time.time()

    output = _model.transfer_style(content_img, style_img)
    new_name = style[style.rfind('/') + 1:] + ' ' + content[content.rfind('/') + 1:]
    output.resize(content_size, Image.ANTIALIAS).save(new_name)
    # теперь отправим назад фото
    print("Done!\ntime taken: {} s".format(int(time.time() - start_time)))
    print(new_name)


if __name__ == '__main__':
    main()
