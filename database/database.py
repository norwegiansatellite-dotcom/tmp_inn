import sqlite3


class DataBase:
    """Класс для взаимодействия с БД"""

    PATH_TO_DATABASE = r'E:\Robots\Checking_INN\database\db.db'

    def __init__(self) -> None:
        """Инициализация параметров"""
        self.connect = sqlite3.connect(self.PATH_TO_DATABASE)
        self.cursor = self.connect.cursor()

    def add_user(self,
                 user_email: str,
                 date_and_time: str,
                 path_to_file: str,
                 status: str
                 ) -> None:
        """
        Добавление пользователя

        Args:
            user_email (str): email пользователя, запросившего выгрузку
            date_and_time (str): дата и время запроса
            path_to_file (str): путь до Excel файла
            status (str): статус (start)
        """
        with self.connect:
            self.cursor.execute(
                "INSERT INTO 'users' (user_email, date_and_time, path_to_file, status) "
                "VALUES (?, ?, ?, ?)",
                (user_email, date_and_time, path_to_file, status))
            self.connect.commit()

    def update_user_status(self, date_and_time: str, status: str) -> None:
        """
        Обновление статуса

        Args:
            date_and_time (str): дата и время
            status (str): статус
        """
        with self.connect:
            self.cursor.execute("UPDATE 'users' SET status = ? WHERE date_and_time = ?",
                                (status, date_and_time))
            self.connect.commit()

    def close_connection(self):
        """Закрытие соединения с БД"""
        self.connect.close()
