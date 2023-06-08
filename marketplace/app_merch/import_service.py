import json
import logging
import os
import shutil

from django.conf import settings
from django.core.mail import EmailMessage

from marketplace.settings import BASE_DIR
from .models import Product

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    filename=os.path.join(BASE_DIR, 'imports', 'results.log'),
    format="%(asctime)s - %(message)s",
)


class ImportProductsService:
    """ Сервис позволяющий работать с импортом товаров. """

    @staticmethod
    def read_data_from_file(filepath):
        """ Метод чтения данных из файла. Ожидается JSON. """

        try:
            with open(filepath, 'r') as f:
                json_data = json.loads(f.read())
            return json_data
        except Exception as e:
            logger.error(f'Could not read data from file: {filepath}. ERROR: {e}')
            return False

    def parse_products(self, filepath):
        """ Метод парсинга и добавления новых товаров. """

        products_data = self.read_data_from_file(filepath=filepath)
        failed = False

        if products_data is False:
            return False

        for index, product in enumerate(products_data):
            try:
                Product.objects.create(
                    title=product['title'],
                    description=product['description'],
                    category_id=product['category_id'],
                    characters=product['characters']
                )

                logger.info(
                    msg=f"INDEX: {index+1} from PATH: {filepath} was SUCCESSFULLY imported."
                )
            except Exception as e:
                logger.error(
                    msg=f"INDEX: {index+1} from PATH: {filepath} was NOT imported. Error: {e}"
                )
                failed = True

        return False if failed else True

    def import_products(self, filepath):
        """ Метод запуска парсинга и переноса файла с данными. """

        if self.parse_products(filepath=filepath):
            result = self.move_file_to_completed_directory(filepath=filepath)
            return True if result else False
        else:
            if filepath.endswith('.json'):
                logger.info(f'REMOVING: {filepath}. INCORRECT DATA')
                os.remove(filepath)
            return False

    @staticmethod
    def move_file_to_completed_directory(filepath):
        """ Метод переноса файла с данными в директорию с готовыми импортами. """

        try:
            if not os.path.exists(os.path.join(BASE_DIR, 'imports', 'completed')):
                os.mkdir(os.path.join(BASE_DIR, 'imports', 'completed'))
            shutil.move(filepath, os.path.join(BASE_DIR, 'imports', 'completed'))
            return True
        except Exception as e:
            logger.error(f'ERROR: {e}')
            return False

    @staticmethod
    def send_log(dst_email: str):
        """ Метод отправки файла с логом на E-mail. """

        try:
            with open(os.path.join(BASE_DIR, 'imports', 'results.log'), 'r') as log_f:
                content = log_f.read()

            email = EmailMessage(
                subject="Результат импортирования товаров.",
                body="Ваши товары были импортированы! Пожалуйста, проверьте лог файл.",
                from_email=settings.EMAIL_HOST_USER,
                to=[dst_email]
            )
            email.attach(
                filename="results.log",
                content=content,
            )
            email.send()
            return True

        except Exception as e:
            logger.error(f'Error while sending E-mail: {e}')
            return False
