import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов в БД'

    def handle(self, **kwargs):
        with open(
            os.path.join(settings.BASE_DIR, 'ingredients.csv'), 'r',
            encoding='UTF-8',
        ) as file:
            reader = csv.reader(file, delimiter=',')
            Ingredient.objects.bulk_create(
                Ingredient(**data) for data in reader
            )
        self.stdout.write(
            self.style.SUCCESS('Ингредиенты загружены в БД')
        )
