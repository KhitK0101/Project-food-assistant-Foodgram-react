import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class import_ingredients(BaseCommand):
    help = 'Импорт ингредиентов в БД'

    def handle(self, **kwargs):
        with open(
            os.path.join(settings.BASE_DIR, '../data/ingredients.csv'), 'r',
            encoding='UTF-8',
        ) as file:
            reader = csv.DictReader(file, delimiter=',')
            ingredients = [Ingredient(**data) for data in reader]
            Ingredient.objects.bulk_create(ingredients)
        self.stdout.write(
            self.style.SUCCESS('Ингредиенты загружены в БД')
        )
