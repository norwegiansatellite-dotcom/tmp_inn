import logging
import os
import socket
import threading
from datetime import datetime

from rocketchat.api import RocketChatAPI


class RocketChat:
    """Класс для работы с Rocket.Chat"""

    def __init__(self):
        """Инициализация параметров"""

        # TODO: смена id_room для Rocket.Chat
        # Для теста: "6697a3eff69caea4bb890619"
        # Для прода: "6662bf8575521c1c13f1b1ec"
        self.id_room = '6697a3eff69caea4bb890619'

        self.rocketChat = RocketChatAPI(
            settings={
                'username': 'Robot_RPA',
                'password': '5rF0JQb7I4',
                'domain': 'https://chat.lime-zaim.ru:30500'
            }
        )

    @staticmethod
    def _is_response_successful(resp: dict) -> bool:
        """
        Проверка статуса отправки сообщения

        :param resp: словарь с ответом на запрос
        :return: True, если отправка успешна, иначе False
        """
        return resp.get('success', False)

    def send_message_with_attachment(self, msg: str, att: str) -> bool:
        """
        Отправка сообщения с вложением

        :param msg: текст сообщения (тип: str)
        :param att: вложение (тип: str)

        :return: результат отправки сообщения (True or False)
        """
        resp = self.rocketChat.upload_file(
            message=msg,
            description="Файл с логом",
            room_id=self.id_room,
            file=att,
        )
        return self._is_response_successful(resp=resp)


class RocketChatHandler(logging.Handler):
    """Кастомный обработчик логирования для отправки сообщений в RocketChat"""

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.rocket_chat = RocketChat()

    def emit(self, record):
        """Отправка сообщения в RocketChat"""
        try:
            log_file_path = self._get_log_file_path()
            formatted_msg = self._format_message()
            self.rocket_chat.send_message_with_attachment(msg=formatted_msg, att=log_file_path)
        except Exception:
            self.handleError(record)

    def _format_message(self) -> str:
        """Форматирование сообщения для отправки в RocketChat"""
        # TODO: Необходимо заменить под своего робота:
        # username_rocket - поставить "@all ," или свой никней
        # name_robot - поставить наименование робота
        username_rocket = '@all ,'
        name_robot = 'Проверка ИНН'

        return (
            f'{username_rocket}\r\n\r\n'
            f'🤖 Робот: `{name_robot}`\r\n'
            f'📝 УЗ: `{os.getlogin()}`\r\n'
            f'💻 Имя сервера: `{socket.gethostname()}\r\n`     '
            f'💻 IP сервера: `{socket.gethostbyname(socket.gethostname())}`\r\n\r\n'
            f'⚡️ Статус: `Произошла ошибка!` 🔴\r\n\r\n'
        )

    def _get_log_file_path(self) -> str:
        """Возвращает полный путь до файла логгера"""
        return self.path_to_file


class CustomLogger:
    """Кастомный логгер"""

    def __init__(self, path_to_folder: str = None, flow_name: str = None, console_output: bool = True) -> None:
        """
        Инициализация параметров

        Args:
            path_to_folder (str, optional): путь до папки. Defaults to None.
            flow_name (str, optional): имя потока для логирования. Defaults to None.
            console_output (bool, optional): вывод информации в консоль (True or False). Defaults to True.
        """
        self.name_folder = 'Log'
        self.current_day = datetime.now().strftime("%d.%m.%Y")

        if path_to_folder:
            self.path_to_folder = os.path.join(os.getcwd(), path_to_folder, self.name_folder)
        else:
            self.path_to_folder = os.path.join(os.getcwd(), self.name_folder, self.current_day)
        self._check_folder_for_log_file()

        if flow_name:
            self.path_to_file = os.path.join(self.path_to_folder, f'{flow_name}.log')
        else:
            current_day_and_time = datetime.now().strftime("%d.%m.%Y__%H_%M_%S")
            self.path_to_file = os.path.join(self.path_to_folder,
                                             f'{threading.current_thread().name}_{current_day_and_time}.log')

        self.log = logging.getLogger(self.path_to_file)

        if not console_output:
            self.console_handler = False
        else:
            self.console_handler = self._setting_for_log_formatter_console()
            self.log.addHandler(self.console_handler)

        self.file_handler = self._setting_for_log_formatter_file()
        self.log.addHandler(self.file_handler)

        # TODO: обработчик для Rocket.Chat
        # self.rocket_chat_handler = RocketChatHandler(level=logging.ERROR)
        # self.rocket_chat_handler.path_to_file = self.path_to_file
        # self.log.addHandler(self.rocket_chat_handler)

        self.log.setLevel(logging.DEBUG)

    def _check_folder_for_log_file(self) -> None:
        """Создание директории для логирования"""
        if not os.path.exists(self.path_to_folder):
            os.makedirs(self.path_to_folder, exist_ok=True)

    def _setting_for_log_formatter_file(self) -> object:
        """Настройка для формата записи файла *.log"""
        file_formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - [%(filename)s] - %(funcName)s: (%(lineno)d) - %(message)s')
        file_handler = logging.FileHandler(self.path_to_file, encoding='UTF-8')
        file_handler.setFormatter(file_formatter)

        return file_handler

    def _setting_for_log_formatter_console(self) -> object:
        """Настройка для вывода данных в консоль"""
        console_formatter = logging.Formatter('[%(asctime)s] - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)

        return console_handler

    def close_logger(self) -> None:
        """Общее закрытие обработчиков (файл, консоль) и удаление их из логгера"""
        self.file_handler.close()
        self.log.removeHandler(self.file_handler)

        if self.console_handler:
            self.console_handler.close()
            self.log.removeHandler(self.console_handler)

        # TODO: закрытие обработчика для Rocket.Chat
        # self.rocket_chat_handler.close()
        # self.log.removeHandler(self.rocket_chat_handler)

    def get_path_to_file_log(self) -> str:
        """Возвращает полный путь до файла логгера"""
        return self.path_to_file

    def start_initialization(self) -> object:
        """Запуск логгера"""
        return self.log
