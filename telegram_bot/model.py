from telegram_bot.model_helpers import *
from telegram_bot.config import Config
import torch
import torch.onnx
from torchvision import models


# В данном классе мы хотим полностью производить всю обработку картинок, которые поступают к нам из телеграма.
# Это всего лишь заготовка, поэтому не стесняйтесь менять имена функций, добавлять аргументы, свои классы и
# все такое.
class StyleTransferModel:
    def __init__(self):
        # Сюда необходимо перенести всю иницализацию, вроде загрузки свеерточной сети и т.д.
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(self.device)

        self.cnn = models.vgg19(pretrained=True).features.eval()

    def transfer_style(self, content_img, style_img):
        # input - PIL images
        # Этот метод по переданным картинкам в каком-то формате (PIL картинка, BytesIO с картинкой
        # или numpy array на ваш выбор). В телеграм боте мы получаем поток байтов BytesIO,
        # а мы хотим спрятать в этот метод всю работу с картинками, поэтому лучше принимать тут эти самые потоки
        # и потом уже приводить их к PIL, а потом и к тензору, который уже можно отдать модели.
        # В первой итерации, когда вы переносите уже готовую модель из тетрадки с занятия сюда нужно просто
        # перенести функцию run_style_transfer (не забудьте вынести инициализацию, которая
        # проводится один раз в конструктор.

        content_img = transformer(content_img)
        style_img = transformer(style_img)
        input_img = content_img.clone()
        output = self._run_style_transfer(self.cnn, cnn_normalization_mean, cnn_normalization_std, content_img,
                                          style_img, input_img, style_weight=Config.STYLE_WEIGHT,
                                          content_weight=Config.CONTENT_WEIGHT)
        return to_image(output)

    def _run_style_transfer(self, cnn, normalization_mean, normalization_std,
                            content_img, style_img, input_img, num_steps=1,
                            style_weight=1000000, content_weight=1):

        def closure():  # python's lambdas have limitations
            # correct the values of updated input image
            input_img.data.clamp_(0, 1)

            optimizer.zero_grad()
            model(input_img)
            style_score = 0
            content_score = 0

            for sl in style_losses:
                style_score += sl.loss
            for cl in content_losses:
                content_score += cl.loss

            style_score *= style_weight
            content_score *= content_weight

            loss = style_score + content_score
            loss.backward()

            run[0] += 1

            return style_score + content_score

        model, style_losses, content_losses = get_style_model_and_losses(cnn, normalization_mean, normalization_std,
                                                                         style_img, content_img, self.device)
        optimizer = get_input_optimizer(input_img)

        run = [0]
        while run[0] <= num_steps:
            print('Step', run)
            optimizer.step(closure)

        # a last correction...
        print("{} steps".format(run[0]))
        input_img.data.clamp_(0, 1)

        return input_img.detach()
