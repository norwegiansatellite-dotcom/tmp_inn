import os
from twocaptcha import TwoCaptcha


def check_balance_RuCpatcha():
    """Проверка баланса RuCpatcha"""

    solver = TwoCaptcha('82820446c4b3836e4edbd665b2e68391')
    balance = solver.balance()

    return balance
