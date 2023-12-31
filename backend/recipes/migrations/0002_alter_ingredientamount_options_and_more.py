# Generated by Django 4.2.3 on 2023-08-06 11:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ingredientamount',
            options={'verbose_name': 'ингредиент', 'verbose_name_plural': 'ингредиенты'},
        ),
        migrations.AlterField(
            model_name='ingredientamount',
            name='ingredient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ingredients_amount', to='recipes.ingredient', verbose_name='ингрединт'),
        ),
    ]
