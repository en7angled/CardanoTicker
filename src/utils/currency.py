from enum import Enum

from src.utils.colors import Colors


class PriceCurrency(Enum):
    USD = "USD"
    BTC = "BTC"
    EUR = "EUR"
    ETH = "ETH"
    ADA = "ADA"

    def get_symbol(self):
        if self == PriceCurrency.USD:
            return "$"
        elif self == PriceCurrency.BTC:
            return "B"  # ₿ $ € Ξ ₳
        elif self == PriceCurrency.EUR:
            return "€"
        elif self == PriceCurrency.ETH:
            return "Ξ"
        elif self == PriceCurrency.ADA:
            return "₳"
        else:
            return "$"

    def get_color(self):
        if self == PriceCurrency.USD:
            return Colors.green.value
        elif self == PriceCurrency.BTC:
            return Colors.orange.value
        elif self == PriceCurrency.EUR:
            return Colors.blue.value
        elif self == PriceCurrency.ETH:
            return Colors.gray.value
        elif self == PriceCurrency.ADA:
            return Colors.light_blue.value
        else:
            return Colors.green.value


def currency_from_str(currency: str) -> PriceCurrency:
    if currency == "usd":
        return PriceCurrency.USD
    elif currency == "eur":
        return PriceCurrency.EUR
    elif currency == "btc":
        return PriceCurrency.BTC
    elif currency == "eth":
        return PriceCurrency.ETH
    elif currency == "ada":
        return PriceCurrency.ADA
    else:
        raise ValueError(f"Invalid currency {currency}")
