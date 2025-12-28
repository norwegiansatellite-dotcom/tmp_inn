import multiprocessing
import os.path
from datetime import timedelta

from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename

from launch_distribution import run_threads
from other import save_user_file

app = Flask(__name__)

app.secret_key = 'ASD&#@^$#JHFSDJHFHdfhsdjfj4435345hjsdfgFfsd^='
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)  # 15 - срок жизни сессии в мин


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/success_request', methods=['POST'])
def success_request():
    # Инициализация данных от пользователя в Web интерфейсе
    _email = request.form['email']
    global email
    email = _email

    file = request.files['file']
    filename = secure_filename(file.filename)

    if filename.endswith('xlsx') or filename.endswith('xls'):
        path_to_file = save_user_file(filename='Данные.xlsx', email=email, file=file)
        global path_to_user_file
        path_to_user_file = path_to_file
        return render_template('success.html')
    else:
        return jsonify({'error': 'Invalid file type'}), 400


def run_threads_in_process(email, path_to_excel, date_and_time):
    run_threads(email=email, path_to_excel=path_to_excel, date_and_time=date_and_time)


@app.route('/start_process', methods=['GET'])
def start_process():
    global path_to_user_file
    global email
    if 'path_to_user_file' in globals():
        process = multiprocessing.Process(target=run_threads_in_process,
                                          args=(email, path_to_user_file, os.path.basename(path_to_user_file)))
        process.start()
        return jsonify({'message': 'Успешно запустил процесс'})
    else:
        return jsonify({'error': 'path_to_user_file not found'}), 400


if __name__ == '__main__':
    app.run(host='localhost', port=44455)
