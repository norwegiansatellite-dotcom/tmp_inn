import os.path
import threading
from datetime import datetime
from time import sleep

import requests
from requests.adapters import HTTPAdapter
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from twocaptcha import TwoCaptcha
from urllib3 import Retry

from logs._logger import CustomLogger
from other import get_full_path_to_folder, update_last_column_excel, get_date_and_time


class BrowserLogger:
    """Логгер для браузера"""

    def __init__(self, path_to_folder: str = None, name_log_file: str = None) -> None:
        """Инициализация параметров"""
        self.path_to_folder = path_to_folder
        self.name_log_file = name_log_file

        if path_to_folder and name_log_file:
            self._set_logger()
        else:
            self.log = self._set_print_logger()

    def _set_logger(self) -> None:
        """Настройка логгера"""
        self.logger = CustomLogger(path_to_folder=self.path_to_folder, flow_name=self.name_log_file)
        self.log = self.logger.start_initialization()

    def _set_print_logger(self) -> object:
        """Настройка логгера с использованием print"""

        class PrintLogger:
            """Кастомная обертка"""

            def info(self, message) -> None:
                print(f"INFO: {message}")

            def error(self, message) -> None:
                print(f"ERROR: {message}")

            def debug(self, message) -> None:
                print(f"DEBUG: {message}")

            def warning(self, message) -> None:
                print(f"WARNING: {message}")

            def critical(self, message) -> None:
                print(f"CRITICAL: {message}")

        return PrintLogger()

    def get_logger(self) -> object:
        """
        Получение объекта логгера

        :return: объект логгера
        """
        return self.log

    def close_logger(self) -> None:
        """Закрытие логгера"""
        if hasattr(self, 'logger'):
            self.logger.close_logger()


class Browser:
    """Класс управления браузером"""

    URL = 'https://service.nalog.ru/inn.do'
    API_TWOCAPTCHA = '82820446c4b3836e4edbd665b2e68391'
    WAITING_TIME_PAGE = 5
    WAITING_TIME_ENTER_WORD = 0.2

    def __init__(self, path_to_excel: str, lock: threading.Lock) -> None:
        """Инициализация параметров"""
        self.path_to_excel = path_to_excel
        self.th_lock = lock

        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_argument("--force-device-scale-factor=0.8")
            self.driver = webdriver.Chrome(options=options)
            # self.driver.set_window_size(1920, 1080)
            self.wait = WebDriverWait(self.driver, self.WAITING_TIME_PAGE)
        except WebDriverException as wd_ex:
            raise Exception(f"Ошибка инициализации драйвера: {wd_ex}")

        self.solver = TwoCaptcha(self.API_TWOCAPTCHA)

    def _send_status_captcha(self, log: object, id_captcha: str, status_code_error: bool) -> None:
        """
        Отправка результатов решения капчи

        Args:
            log (object):
            id_captcha (str): id капчи
            status_code_error (bool): True - если ошибка, False - если решено верно
        """
        try:
            if status_code_error:
                self.solver.report(id_captcha, False)
            else:
                self.solver.report(id_captcha, True)
        except Exception as ex_send_status:
            log.info(f'Ошибка при отправке статуса капчи: {ex_send_status}')

    def _take_screenshot(self, name_file: str) -> None:
        """
        Сохранение скриншота

        :param name_file: наименование файла
        """
        try:
            path_to_save_screen = os.path.dirname(self.path_to_excel)
            dir_name_save_screen = 'error'
            file_name_save_screen = f'{name_file}.png'
            full_path_to_screen_error = os.path.join(path_to_save_screen, dir_name_save_screen)
            new_full_path_to_screen_error = get_full_path_to_folder(new_folder=full_path_to_screen_error)
            full_path_to_screen = os.path.join(new_full_path_to_screen_error, file_name_save_screen)
            self.driver.save_screenshot(full_path_to_screen)
        except Exception as ex:
            # Если сохранение скриншота не удалось, логируем ошибку и продолжаем
            print(f"ERROR: Не удалось сохранить скриншот: {ex}")

    def verification_personal_data(self) -> None:
        """Соглашение о персональных данных"""
        try:
            sleep(self.WAITING_TIME_PAGE)
            # Нажатие на галочку
            self.driver.find_element(By.ID, 'unichk_0').click()
            sleep(1)
            # Нажатие на "Продолжить"
            self.driver.find_element(By.ID, 'btnContinue').click()
            sleep(self.WAITING_TIME_PAGE)
        except Exception as ex:
            log_path = os.path.join(os.getcwd(), 'logs', 'error')
            _ex_logger = CustomLogger(path_to_folder=log_path)
            ex_log = _ex_logger.start_initialization()
            ex_log.info('Завершаю работу из-за ошибки загрузки сайта')
            ex_log.error(f'Ошибка при загрузке сайта: {ex}')
            _ex_logger.close_logger()
            self._take_screenshot(name_file=datetime.now().strftime("%H_%M_%S"))
            raise Exception('Остановка работы из-за ошибки загрузки сайта')

    def _enter_full_name(self, full_name: str, log: object) -> None:
        """
        Ввод ФИО в поля на сайте

        :param full_name (str): ФИО клиента
        """
        try:
            log.info('Ввожу ФИО клиента')
            full_name_split = full_name.split()

            last_name = full_name_split[0]
            name = full_name_split[1]
            try:
                surname = full_name_split[2]
            except IndexError:
                log.info('У клиента нет отчества')
                surname = None

            # Ввод Фамилии
            elem_last_name = self.driver.find_element(By.ID, 'fam')
            elem_last_name.clear()
            for char in last_name:
                elem_last_name.send_keys(char)
                sleep(self.WAITING_TIME_ENTER_WORD)

            # Ввод Имени
            elem_name = self.driver.find_element(By.ID, 'nam')
            elem_name.clear()
            for char in name:
                elem_name.send_keys(char)
                sleep(self.WAITING_TIME_ENTER_WORD)

            # Ввод Отчества или отмечаем его отсутствие
            if surname:
                elem_surname = self.driver.find_element(By.ID, 'otch')
                elem_surname.clear()
                for char in surname:
                    elem_surname.send_keys(char)
                    sleep(self.WAITING_TIME_ENTER_WORD)
            else:
                try:
                    self.driver.find_element(By.ID, 'unichk_0').click()
                except Exception as ex_inner:
                    log.info(f'Ошибка при установке флага отсутствия отчества: {ex_inner}')
        except Exception as ex:
            log.info(f'Ошибка при вводе ФИО: {ex}')
            self._take_screenshot(name_file=f'full_name_{full_name}')
            raise

    def _enter_date_of_birth(self, date_of_birth: str, log: object) -> None:
        """
        Ввод даты рождения в поле на сайте

        :param date_of_birth: дата рождения клиента
        """
        try:
            log.info('Ввожу дату рождения')
            if len(date_of_birth) >= 19:
                date_object = datetime.strptime(date_of_birth, "%Y-%m-%d %H:%M:%S")
                formatted_date = date_object.strftime("%d.%m.%Y")
            else:
                formatted_date = date_of_birth
            elem_date_birth = self.driver.find_element(By.ID, 'bdate')
            elem_date_birth.clear()
            for char in formatted_date:
                elem_date_birth.send_keys(char)
                sleep(self.WAITING_TIME_ENTER_WORD)
        except Exception as ex:
            log.info(f'Ошибка при вводе даты рождения: {ex}')
            raise

    def _enter_passport_data(self, passport_data: str, log: object) -> None:
        """
        Ввод серии и номера паспорта

        :param passport_data: серия и номер паспорта
        """
        try:
            log.info('Ввожу серию и номер паспорта')
            elem_passport = self.driver.find_element(By.ID, 'docno')
            elem_passport.clear()
            for char in passport_data:
                elem_passport.send_keys(char)
                sleep(self.WAITING_TIME_ENTER_WORD)
        except Exception as ex:
            log.info(f'Ошибка при вводе паспортных данных: {ex}')
            raise

    def _send_request_button(self, log: object) -> None:
        """Нажатие на кнопку Отправить запрос"""
        try:
            log.info("Отправляю запрос на проверку")
            self.driver.find_element(By.ID, 'btn_send').click()
        except Exception as ex:
            log.info(f'Ошибка при нажатии кнопки отправки запроса: {ex}')
            raise

    def _get_inn_on_site(self, log: object, full_name: str, passport_data: str) -> bool | tuple[bool, str]:
        """
        Проверка корректности ИНН

        :param log: объект логирования
        :param full_name: ФИО клиента
        :param passport_data: паспортные данные клиента

        :return: True - найден ИНН, False - ИНН не найден или ошибка
        """
        try:
            log.info('Начинаю проверку ИНН')
            sleep(self.WAITING_TIME_PAGE)
            self.driver.switch_to.default_content()
            col_left_75 = self.driver.find_element(By.CLASS_NAME, 'col-left-75')
            inn_on_site = col_left_75.find_element(By.ID, 'resultInn').text

            if inn_on_site == '':
                log.info('Введены некорректные данные')
                update_last_column_excel(
                    path_to_excel=self.path_to_excel,
                    inn_on_site='ИНН не найден',
                    passport_data=passport_data,
                    full_name=full_name,
                    log=log,
                    lock=self.th_lock
                )
                return False
            else:
                log.info('Смог найти ИНН')
                update_last_column_excel(
                    path_to_excel=self.path_to_excel,
                    inn_on_site=inn_on_site,
                    passport_data=passport_data,
                    full_name=full_name,
                    log=log,
                    lock=self.th_lock
                )
                return True
        except NoSuchElementException:
            log.info('Не удалось найти элемент с ИНН')
            return False
        except Exception as ex:
            log.info(f'Непредвиденная ошибка при получении ИНН: {ex}')
            return False

    def _set_logger(self, path_to_folder: str, name_log_file: str) -> object:
        """
        Настройка логгера

        :param path_to_folder: путь до папки для логов
        :param name_log_file: наименование файла
        :return: объект логгера
        """
        return BrowserLogger(path_to_folder=path_to_folder, name_log_file=name_log_file)

    def _check_warning_window(self, log: object) -> str:
        """
        Проверка всплывающих окон

        :param log: объект логгирования
        :return: статус окна ("ok", "captcha", "empty_window")
        """
        try:
            log.info('Проверяю всплывающие окна')
            title_text = self.driver.find_element(By.ID, 'dialogHead').text
            if title_text == 'УВАЖАЕМЫЙ ПОЛЬЗОВАТЕЛЬ!':
                log.info(f'Обнаружено окно "{title_text}", закрываю его')
                self.driver.find_element(By.ID, 'btnClose').click()
                sleep(self.WAITING_TIME_PAGE)
                self.driver.switch_to.default_content()
                self._send_request_button(log=log)
                return 'empty_window'
            elif title_text == 'ВВЕДИТЕ ЦИФРЫ С КАРТИНКИ':
                log.info(f'Обнаружено окно капчи "{title_text}"')
                return 'captcha'
            else:
                log.info(f'Неожиданное окно: "{title_text}"')
                return 'ok'
        except NoSuchElementException:
            log.info('Всплывающее окно не обнаружено, продолжаю работу')
            return 'ok'
        except Exception as ex:
            log.info(f'Ошибка при проверке всплывающего окна: {ex}')
            return 'ok'

    def _get_code_captcha(self, log: object, path_to_image_captcha: str) -> tuple:
        """
        Получение id и кода капчи

        Args:
            log (object): логгер
            path_to_image_captcha (str): путь до изображения капчи

        Returns:
            tuple: id капчи и код решения
        """
        try:
            log.info('Отправляю запрос на решение капчи')
            result = self.solver.normal(path_to_image_captcha)
            return result['captchaId'], result['code']
        except Exception as ex:
            log.info(f'Ошибка при получении кода капчи: {ex}')
            self._take_screenshot(name_file=f'code_captcha_{datetime.now().strftime("%h_%m_%s")}')
            raise

    def _save_image_captcha(self, log: object) -> str | None:
        """
        Скачивание изображения капчи

        :return: путь до сохраненного изображения или None в случае ошибки
        """
        try:
            captcha_image_element = self.driver.find_element(By.CSS_SELECTOR, 'div.captcha-block img')
            captcha_image_url = captcha_image_element.get_attribute('src')

            retry_strategy = Retry(
                total=5,
                status_forcelist=[429, 500, 502, 503, 504],
                backoff_factor=1
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            http = requests.Session()
            http.mount("https://", adapter)
            http.mount("http://", adapter)

            response = http.get(captcha_image_url, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            log.info(f'Ошибка загрузки изображения капчи: {e}')
            return None
        except Exception as ex:
            log.info(f'Ошибка при сохранении изображения капчи: {ex}')
            return None

        try:
            date_and_time = get_date_and_time()
            path_to_folder_screen = os.path.join(os.getcwd(), 'screenshot_captcha')
            if not os.path.exists(path_to_folder_screen):
                os.makedirs(path_to_folder_screen, exist_ok=True)

            path_to_file_captcha = os.path.join(path_to_folder_screen, f'{date_and_time}.png')
            with open(path_to_file_captcha, 'wb') as file:
                file.write(response.content)
            return path_to_file_captcha
        except Exception as ex:
            log.info(f'Ошибка при записи файла капчи: {ex}')
            return None

    def _checking_correctness_input_code_captcha(self, log: object) -> bool:
        """
        Проверка правильности ввода капчи

        :param log: объект логгирования
        :return: True если капча решена правильно, иначе False
        """
        try:
            log.info('Проверяю правильность введённой капчи')
            error_text = self.driver.find_element(By.ID, 'errors_captcha').text
            if error_text == 'Цифры с картинки введены неверно':
                log.info('Капча решена неверно, обновляю изображение капчи')
                try:
                    self.driver.find_element(By.LINK_TEXT, "Обновить картинку с цифрами").click()
                except Exception as e:
                    log.info(f'Ошибка при обновлении капчи: {e}')
                sleep(2)
                return False
            else:
                return True
        except NoSuchElementException:
            log.info('Сообщение об ошибке капчи не найдено, продолжаю работу')
            self.driver.switch_to.default_content()
            return True
        except Exception as ex:
            log.info(f'Ошибка при проверке капчи: {ex}')
            return False

    def _captcha_input(self, log: object, code_captcha: str) -> str:
        """
        Ввод решения капчи

        :param log: объект логгирования
        :param code_captcha: решение капчи
        :return: строка с кодом ошибки ("error", "ok", "system_error")
        """
        try:
            log.info(f'Ввожу решение капчи: {code_captcha}')
            elem_captcha = self.driver.find_element(By.ID, 'captcha')
            elem_captcha.clear()
            for char in code_captcha:
                elem_captcha.send_keys(char)
                sleep(self.WAITING_TIME_ENTER_WORD)
            self.driver.find_element(By.ID, 'btnOk').click()
            sleep(self.WAITING_TIME_PAGE)
            if not self._checking_correctness_input_code_captcha(log=log):
                return 'error'
            else:
                return 'ok'
        except Exception as ex:
            log.info(f'Ошибка при вводе капчи: {ex}')
            return 'system_error'

    def _reCheck_window(self, log: object) -> str:
        try:
            sleep(self.WAITING_TIME_PAGE)
            frames = self.driver.find_elements(By.TAG_NAME, 'iframe')
            if len(frames) >= 1:
                self.driver.switch_to.frame(0)
                check_window = self._check_warning_window(log=log)
                if check_window == 'empty_window':
                    log.info('Окно "УВАЖАЕМЫЙ ПОЛЬЗОВАТЕЛЬ!" не исчезло')
                    return 'empty_window'
                elif check_window == 'captcha':
                    return 'captcha'
                elif check_window == 'ok':
                    return 'ok'
            else:
                return ''
        except Exception as ex:
            log.info(f'Ошибка при перепроверке окна: {ex}')
            return ''

    def _check_captcha(self, log: object) -> bool:
        try:
            while True:
                check_window = self._reCheck_window(log=log)
                if check_window == 'empty_window':
                    continue
                elif check_window == 'captcha':
                    for count in range(1, 5):
                        if count == 4:
                            # Превышено число попыток
                            return False
                        path_to_file_captcha = self._save_image_captcha(log=log)
                        if path_to_file_captcha is None:
                            return False
                        log.info(f'Попытка решения капчи № {count}')
                        id_captcha, code_captcha = self._get_code_captcha(
                            log=log, path_to_image_captcha=path_to_file_captcha
                        )
                        status = self._captcha_input(log=log, code_captcha=code_captcha)
                        if status == 'ok':
                            self._send_status_captcha(log=log, id_captcha=id_captcha, status_code_error=False)
                            return True
                        elif status == 'error':
                            self._send_status_captcha(log=log, id_captcha=id_captcha, status_code_error=True)
                        elif status == 'system_error':
                            return False
                elif check_window == 'ok':
                    return True
                else:
                    log.info('Всплывающих окон не обнаружено')
                    return True
        except Exception as ex:
            log.info(f'Ошибка при проверке капчи: {ex}')
            return False

    def start_checking_inn(self, dataframe: list[list[str]]):
        """
        Запуск проверки ИНН у клиента

        :param dataframe: список данных из Excel файла
        """
        full_name = ''

        try:
            self.driver.get(self.URL)
        except Exception as ex:
            print(f"Ошибка при переходе на страницу {self.URL}: {ex}")
            return

        try:
            self.verification_personal_data()
        except Exception as ex:
            print(f"Ошибка при верификации персональных данных: {ex}")
            return

        path_to_folder = os.path.dirname(self.path_to_excel)

        for data in dataframe:
            try:
                full_name = data[-4]
                date_of_birth = data[-3]
                passport_data = f'{data[-2]}{data[-1]}'

                logger = self._set_logger(path_to_folder=path_to_folder, name_log_file=full_name)
                log = logger.get_logger()
                log.info(f'Запуск проверки ИНН для клиента: {full_name}')

                try:
                    self._enter_full_name(full_name=full_name, log=log)
                except Exception as ex:
                    log.info(f'Ошибка ввода ФИО: {ex}')
                    continue

                try:
                    self._enter_date_of_birth(date_of_birth=date_of_birth, log=log)
                except Exception as ex:
                    log.info(f'Ошибка ввода даты рождения: {ex}')
                    continue

                try:
                    self._enter_passport_data(passport_data=passport_data, log=log)
                except Exception as ex:
                    log.info(f'Ошибка ввода паспортных данных: {ex}')
                    continue

                try:
                    self._send_request_button(log=log)
                except Exception as ex:
                    log.info(f'Ошибка при нажатии кнопки отправки запроса: {ex}')
                    continue

                sleep(self.WAITING_TIME_PAGE)

                if not self._check_captcha(log=log):
                    log.info('Не удалось решить капчу, пропускаю клиента')
                    continue

                check_inn = self._get_inn_on_site(log=log, full_name=full_name, passport_data=passport_data)
                if not check_inn:
                    self._take_screenshot(name_file=full_name)

                # Очищаем форму запроса
                try:
                    self.driver.find_element(By.ID, 'btn_reset').click()
                except Exception as ex_er:
                    log.info(f'Ошибка при нажатии кнопки очистки формы: {ex_er}')
                sleep(2)

                try:
                    # Если появляется alert, пробуем его закрыть
                    alert_ok = self.driver.switch_to.alert
                    alert_ok.accept()
                except Exception as ex_alert:
                    log.info(f'Ошибка при обработке alert: {ex_alert}')

                sleep(3)
                logger.close_logger()
                self.driver.refresh()

            except Exception as ex_client:
                self._take_screenshot(name_file=f'ERROR_{full_name}')
                self.driver.refresh()
                sleep(3)
                continue

        try:
            self.driver.close()
            self.driver.quit()
        except Exception as ex:
            print(f"Ошибка при закрытии драйвера: {ex}")
