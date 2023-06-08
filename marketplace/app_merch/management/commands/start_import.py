import os

from django.conf import settings
from django.core.management.base import BaseCommand

from app_merch.tasks import make_an_products_importation


class Command(BaseCommand):
    """
    Кастомная management команда для импортирования товаров из JSON файлов.
    """

    help = "Import products from JSON files."

    def add_arguments(self, parser):
        """
        Аргумент 'files' для команды:
        Является опциональным, пример:
        python manage.py start_import apple.json samsung.json
        """

        parser.add_argument(
            "files", nargs="*", type=str, default=[], help="List of files to import from"
        )

    def handle(self, *args, **options):
        file_list = options["files"] if options["files"] else os.listdir(
            os.path.join(settings.BASE_DIR, 'imports', 'waiting')
        )

        for file in file_list:
            filepath = os.path.join(settings.BASE_DIR, 'imports', 'waiting', file)
            res = make_an_products_importation.delay(filepath=filepath).get()
            self.stdout.write(
                self.style.SUCCESS(f"SUCCESSFULLY imported: {file}")
            ) if res else self.stderr.write(
                self.style.ERROR(f"FAILED to import: {file}")
            )
