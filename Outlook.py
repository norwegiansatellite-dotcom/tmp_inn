import os
import smtplib
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Outlook:
    """Отправка письма через SMTP"""

    def __init__(self) -> None:
        """Инициализация параметров"""

        smtp_server = 'mail.lime.local'
        smtp_port = 10666

        self.sender_email = 'lcgs_r_000015@lime.local'  # Логин от почты
        self.password = 'HTO4zb#pB((Vs2V'  # Пароль от почты

        self.msg = MIMEMultipart()
        self.server = smtplib.SMTP(smtp_server, smtp_port)

    def _attachment(self, attachment_path: str) -> None:
        """Прикрепление вложений к письму"""
        with open(attachment_path, 'rb') as attachment:
            part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            filename = os.path.basename(attachment_path)
            part.add_header('Content-Disposition',
                            'attachment; filename="{}"'.format(Header(filename, 'utf-8').encode()))
            self.msg.attach(part)

    def _send_mail(self, msg_to: list) -> bool:
        """Отправка письма"""
        try:
            self.server.starttls()
            self.server.login(self.sender_email, self.password)
            text = self.msg.as_string()
            self.server.sendmail(self.sender_email, msg_to, text)
            return True
        except Exception as e:
            print(f"Ошибка: {e}")
            return False

    def send_mail(self, mail_to: list, path_to_folder: str) -> bool:
        """Внешний метод отправки письма"""
        self.msg['From'] = self.sender_email
        self.msg['Subject'] = 'Результат отчёта проверки ИНН'
        self.msg['To'] = ', '.join(mail_to)

        formatted_path = path_to_folder.replace('\\', '/')
        html_body = f"""
        <html>
            <body>
                <p>Добрый день!</p>
                <p>Робот по проверке ИНН отработал, можете посмотреть резултат:</p>
                <br>
                <a href="file:///{formatted_path}">Открыть папку</a>
            </body>
        </html>
        """
        self.msg.attach(MIMEText(html_body, 'html'))

        return self._send_mail(msg_to=mail_to)

    def send_mail_error(self, mail_to: list) -> bool:
        """Внешний метод отправки письма"""
        self.msg['From'] = self.sender_email
        self.msg['Subject'] = 'Некорректный файл'
        self.msg['To'] = ', '.join(mail_to)

        html_body = f"""
        <html>
            <body>
                <p>Добрый день!</p>
                <p>Робот по проверке ИНН не смог отработать, т.к. вы прикрепили некорректный файл!</p>
                <p>Посмотрите, пожалуйста, описание робота:
                <a href="https://confluence.lcgs.ru/pages/viewpage.action?pageId=3709496509">Открыть ссылку</a>
            </body>
        </html>
        """
        self.msg.attach(MIMEText(html_body, 'html'))

        return self._send_mail(msg_to=mail_to)
