import os
from PIL import Image, ImageFont, ImageDraw
from typing import Tuple, List


from src.widgets.generic.w_abstract import AbstractWidget, ImageWidget
from src.data_fetcher.data_fetcher import DataFetcher
from src.utils.currency import PriceCurrency
from src.utils.colors import Colors
from src.utils.constants import RESOURCES_DIR


class LogoBtc(ImageWidget):
    def __init__(self, size: Tuple[int, int], background_color=Colors.white.value):
        """
        Initialize the widget
        Args:
            size: The size of the widget in pixels, (width, height)
        """
        logo_path = os.path.join(RESOURCES_DIR, "logos/btclogo.png")
        super().__init__(size, Image.open(logo_path))
        self.background_color = background_color


class LogoEth(ImageWidget):
    def __init__(self, size: Tuple[int, int], background_color=Colors.white.value):
        """
        Initialize the widget
        Args:
            size: The size of the widget in pixels, (width, height)
        """
        logo_path = os.path.join(RESOURCES_DIR, "logos/eth.png")
        super().__init__(size, Image.open(logo_path))
        self.background_color = background_color


class LogoAda(ImageWidget):
    def __init__(self, size: Tuple[int, int], background_color=Colors.white.value):
        """
        Initialize the widget
        Args:
            size: The size of the widget in pixels, (width, height)
        """
        logo_path = os.path.join(RESOURCES_DIR, "logos/cardano_log.png")
        super().__init__(size, Image.open(logo_path))
        self.background_color = background_color


class PriceWidget(AbstractWidget):
    def __init__(
        self,
        price: float,
        size: Tuple[int, int],
        currency: PriceCurrency,
        text_color=Colors.black.value,
        background_color=Colors.white.value,
    ):
        """
        Initialize the widget
        Args:
            price: The price of the Coin
            currency: The currency of the price
            text_color: The color of the text
            background_color: The background color of the widget
        """
        super().__init__(size, background_color)
        self._price = price
        self._currency = currency
        self._text_color = self._convert_color(text_color)
        # Load the font
        self.font_path = os.path.join(RESOURCES_DIR, "fonts/DejaVuSans.ttf")
        self.load_font(size=self.height)

    property

    def currency(self):
        return self._currency

    @staticmethod
    def format_number_to_text(number, n):
        """
        Converts a number to text with fixed precision or exponential notation.

        Args:
            number: The number to convert.
            n: The maximum number of characters for the output.

        Returns:
            The text representation of the number, or None if input is invalid.
        """

        if not isinstance(number, (int, float)):
            return None

        if number >= 1:
            for precision in range(n - 1, -1, -1):  # Try decreasing precision
                formatted = f"{number:.{precision}f}".rstrip("0").rstrip(".")
                if len(formatted) <= n:
                    return formatted.ljust(n)
            return f"{number:.{n-4}e}".ljust(
                n
            )  # If even 0 precision is too long, use exponential. Leave space for e+XX

        else:  # number < 1
            formatted = str(number).rstrip("0").rstrip(".")
            if len(formatted) <= n:
                return formatted.ljust(n)
            else:
                formatted = f"{number:.{max(n-4-2,0)}e}"
                if len(formatted) <= (n + 1):
                    return formatted.ljust(n)

            return None  # No suitable representation found

    def __load_adjusted_font(self, text, font, size: Tuple[int, int]):
        """
        Adjust the font size to fit the text within the width
        Args:
            text: The text to fit
            font: The font to use
            size: The size of the widget in pixels, (width, height) to fit the text in
        """
        # find number of lines in text
        nb_lines = text.count("\n") + 1
        get_longest_line = max(text.split("\n"), key=len)

        f_size = font.getsize(get_longest_line)
        while f_size[0] > size[0] or nb_lines * f_size[1] > size[1]:
            font.size -= 1
            font = ImageFont.truetype(self.font_path, font.size)
            f_size = font.getsize(get_longest_line)

        return font

    def update(self, price: float):
        """
        Update the price
        Args:
            price: The price of the coin
        """
        self._price = price
        self.render()

    def load_font(self, size):
        """
        Load the font
        """
        self.font_size = size
        self.font = ImageFont.truetype(self.font_path, self.font_size)

    def render(self):
        """
        Render the widget
        """

        self._canvas = Image.new("RGBA", self.resolution, self.background_color)
        img_canvas = self._canvas
        draw = ImageDraw.Draw(img_canvas)

        # Draw the price, ensure it is formatted with commas and maximum of 5 characters
        price_txt = PriceWidget.format_number_to_text(self._price, n=8)
        # price_txt=price_txt.replace(" ", "#")

        # adjust the font size to fit the price
        self.font = self.__load_adjusted_font(
            price_txt + " " + self._currency.get_symbol(), self.font, self._size
        )
        self.font_size = self.font.size

        t_offset = (self.height - self.font_size) // 2

        # replace("#", "\u00A0")
        draw.text((5, t_offset), price_txt, self._text_color, font=self.font)

        # Draw the currency sign
        symbol = self._currency.get_symbol()
        symbol_color = self._currency.get_color()
        start_pos = self.font.getsize(price_txt)[0] + 5
        draw.text((start_pos, t_offset), symbol, symbol_color, font=self.font)


class BtcPrice(PriceWidget):
    def __init__(
        self,
        data_fetcher: DataFetcher,
        size: Tuple[int, int],
        currency=PriceCurrency.USD,
        background_color=Colors.white.value,
        text_color=Colors.black.value,
    ):
        """
        Initialize the widget
        Args:
            data_fetcher: The data fetcher to get the price
            size: The size of the widget in pixels, (width, height)
            currency: The currency to compare the coin to
            background_color: The background color of the widget
        """
        self.data_fetcher = data_fetcher
        price = data_fetcher.get_realtime("BTC", currency.value)
        super().__init__(price, size, currency, text_color, background_color)

    def update(self):
        price = self.data_fetcher.get_realtime("BTC", self._currency.value)
        return super().update(price)


class EthPrice(PriceWidget):
    def __init__(
        self,
        data_fetcher: DataFetcher,
        size: Tuple[int, int],
        currency=PriceCurrency.USD,
        background_color=Colors.white.value,
        text_color=Colors.black.value,
    ):
        """
        Initialize the widget
        Args:
            data_fetcher: The data fetcher to get the price
            size: The size of the widget in pixels, (width, height)
            currency: The currency to compare the coin to
            background_color: The background color of the widget
        """
        self.data_fetcher = data_fetcher
        price = data_fetcher.get_realtime("ETH", currency.value)
        super().__init__(price, size, currency, text_color, background_color)

    def update(self):
        price = self.data_fetcher.get_realtime("ETH", self._currency.value)
        return super().update(price)


class AdaPrice(PriceWidget):
    def __init__(
        self,
        data_fetcher: DataFetcher,
        size: Tuple[int, int],
        currency=PriceCurrency.USD,
        background_color=Colors.white.value,
        text_color=Colors.black.value,
    ):
        """
        Initialize the widget
        Args:
            data_fetcher: The data fetcher to get the price
            size: The size of the widget in pixels, (width, height)
            currency: The currency to compare the coin to
            background_color: The background color of the widget
        """
        self.data_fetcher = data_fetcher
        price = data_fetcher.get_realtime("ADA", currency.value)
        super().__init__(price, size, currency, text_color, background_color)

    def update(self):
        price = self.data_fetcher.get_realtime("ADA", self._currency.value)
        return super().update(price)


class PriceWithLogo(AbstractWidget):
    def __init__(
        self,
        prices: List[Tuple[float, PriceCurrency]],
        size: Tuple[int, int],
        logo: ImageWidget,
        text_color=Colors.black.value,
        background_color=Colors.white.value,
    ):
        """
        Initialize the widget
        Args:
            prices: The price of the Coin, a li
            size: The size of the widget in pixels, (width, height)
            logo: The logo of the coin
            text_color: The color of the text
            background_color: The background color of the widget
        """
        super().__init__(size, background_color)
        self.logo = logo
        self.logo_size = (size[1], size[1])

        nb_elements = len(prices)
        if nb_elements == 1:
            price_size = (size[0] - self.logo_size[0], size[1])
            self.price_widgets = {
                prices[0][1]: PriceWidget(
                    prices[0][0], price_size, prices[0][1], text_color, background_color
                )
            }
            self.main_currency = prices[0][1]
        else:
            self.price_widgets = dict()
            for i, (price, currency) in enumerate(prices):
                if i == 0:
                    self.main_currency = currency
                    price_size = (
                        size[0] - self.logo_size[0],
                        2 * size[1] // (nb_elements + 1),
                    )
                else:
                    price_size = (
                        size[0] - self.logo_size[0],
                        size[1] // (nb_elements + 1),
                    )
                self.price_widgets[currency] = PriceWidget(
                    price, price_size, currency, text_color, background_color
                )

    def update(self, prices: List[Tuple[float, PriceCurrency]]):
        """
        Update the price
        Args:
            price: The price of the coin
        """
        for price, currency in prices:
            self.price_widgets[currency].update(price)
        self.render()

    def render(self):
        """
        Render the widget
        """
        self._canvas = Image.new("RGBA", self.resolution, self.background_color)
        img_canvas = self._canvas

        self.logo.render()
        for currency, price_widget in self.price_widgets.items():
            price_widget.render()

        img_canvas.paste(self.logo.get(), (0, 0), mask=self.logo.get())
        main_price_widget = self.price_widgets[self.main_currency]
        img_canvas.paste(main_price_widget.get(), (self.logo_size[0], 0))

        last_height = main_price_widget.height
        for currency, currency_widget in self.price_widgets.items():
            if currency != self.main_currency:
                img_canvas.paste(
                    currency_widget.get(), (self.logo_size[0], last_height)
                )
                last_height += currency_widget.height


class CoinPriceWithLogo(PriceWithLogo):
    def __init__(
        self,
        data_fetcher: DataFetcher,
        size: Tuple[int, int],
        currency=PriceCurrency.USD,
        background_color=Colors.white.value,
        text_color=Colors.black.value,
    ):
        """
        Initialize the widget
        Args:
            data_fetcher: The data fetcher to get the price
            size: The size of the widget in pixels, (width, height)
            currency: The currency to compare the coin to, a list of currencies or a single currency
            background_color: The background color of the widget
        """
        self.data_fetcher = data_fetcher
        self._size = size
        self.background_color = background_color
        logo = self.get_logo()
        symbol = self.get_symbol()

        if isinstance(currency, list):
            prices = [(data_fetcher.get_realtime(symbol, c.value), c) for c in currency]
        else:
            prices = [(data_fetcher.get_realtime(symbol, currency.value), currency)]
        super().__init__(prices, size, logo, text_color, background_color)

    def get_logo(self):
        raise NotImplementedError("Subclasses must implement the get_logo method")

    def get_symbol(self):
        raise NotImplementedError("Subclasses must implement the get_symbol method")

    def update(self):
        symbol = self.get_symbol()
        prices = [
            (self.data_fetcher.get_realtime(symbol, c.value), c)
            for c in self.price_widgets.keys()
        ]
        return super().update(prices)


class BtcPriceWithLogo(CoinPriceWithLogo):
    def __init__(
        self,
        data_fetcher,
        size,
        currency=PriceCurrency.USD,
        background_color=Colors.white.value,
        text_color=Colors.black.value,
    ):
        super().__init__(data_fetcher, size, currency, background_color, text_color)

    def get_logo(self):
        size = self.resolution
        return LogoBtc((size[1], size[1]), background_color=self.background_color)

    def get_symbol(self):
        return "BTC"


class EthPriceWithLogo(CoinPriceWithLogo):
    def __init__(
        self,
        data_fetcher,
        size,
        currency=PriceCurrency.USD,
        background_color=Colors.white.value,
        text_color=Colors.black.value,
    ):
        super().__init__(data_fetcher, size, currency, background_color, text_color)

    def get_logo(self):
        size = self.resolution
        return LogoEth((size[1], size[1]), background_color=self.background_color)

    def get_symbol(self):
        return "ETH"


class AdaPriceWithLogo(CoinPriceWithLogo):
    def __init__(
        self,
        data_fetcher,
        size,
        currency=PriceCurrency.USD,
        background_color=Colors.white.value,
        text_color=Colors.black.value,
    ):
        super().__init__(data_fetcher, size, currency, background_color, text_color)

    def get_logo(self):
        size = self.resolution
        return LogoAda((size[1], size[1]), background_color=self.background_color)

    def get_symbol(self):
        return "ADA"
