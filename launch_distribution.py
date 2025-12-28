import os.path
import random
import threading
import time

from Outlook import Outlook
from browser import Browser
from other import get_data_from_excel, copy_result_folder_to_public_folder, check_null_clients


def start_process_browser(path_to_excel: str, data_chunk, lock: threading.Lock):
    Browser(path_to_excel=path_to_excel, lock=lock).start_checking_inn(dataframe=data_chunk)


# Функция для запуска потоков
def run_threads(email: str, path_to_excel: str, date_and_time: str):
    # TODO: количество потоков
    num_threads = 1

    lock = threading.Lock()

    all_data_from_excel = get_data_from_excel(path_to_excel=path_to_excel, email=email)

    if len(all_data_from_excel) < num_threads:
        num_threads = len(all_data_from_excel)

    chunk_size = len(all_data_from_excel) // num_threads
    data_chunks = [all_data_from_excel[i * chunk_size:(i + 1) * chunk_size] for i in range(num_threads)]

    # Если остались данные, добавляем их к последнему списку
    if len(all_data_from_excel) % num_threads != 0:
        data_chunks[-1].extend(all_data_from_excel[num_threads * chunk_size:])

    threads = []
    for data_chunk in data_chunks:
        sleep_time = random.uniform(3, 8)
        time.sleep(sleep_time)

        thread = threading.Thread(target=start_process_browser, args=(path_to_excel, data_chunk, lock))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # TODO: повторная проверка
    repeated_customer_data = check_null_clients(path_to_file=path_to_excel)

    count_attemp = 0
    while len(repeated_customer_data) > 0:
        if count_attemp > 5:
            break

        thread = threading.Thread(target=start_process_browser, args=(path_to_excel, repeated_customer_data, lock))
        thread.start()
        thread.join()

        repeated_customer_data = check_null_clients(path_to_file=path_to_excel)
        count_attemp += 1

    # TODO: копирование данных на общий диск
    path_to_folder = os.path.dirname(path_to_excel)
    public_folder = copy_result_folder_to_public_folder(
        path_to_local_folder=path_to_folder,
        email=email
    )

    # TODO: отправка email о готовности
    if public_folder:
        Outlook().send_mail(
            mail_to=[email],
            path_to_folder=public_folder
        )
