from colorfield.fields import ColorField
from django.core import validators
from django.conf import settings
from django.db import models
from django.db.models import Exists, OuterRef

from users.models import User


class Ingredient(models.Model):
    name = models.CharField(
        blank=False,
        max_length=settings.LENGTH_MAX,
        verbose_name='Название',
    )
    measurement_unit = models.CharField(
        blank=False,
        max_length=settings.LENGTH_MAX,
        verbose_name='Единицы измерения',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Tag(models.Model):
    name = models.CharField(
        max_length=settings.LENGTH_NAME_COLOR,
        unique=True,
        verbose_name='Имя тега',
    )
    color = ColorField(
        max_length=settings.LENGTH_COLOR,
        unique=True,
        verbose_name='Цвет (HEX code)',
        help_text='Пример, #4B0082',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='URL',
        help_text='Уникальный URL-адрес для тега',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class RecipeQuerySet(models.QuerySet):

    def filter_tags(self, tags):
        if tags:
            return self.filter(tags__slug__in=tags).distinct()
        return self

    def add_user_annotations(self, user_id):
        return self.annotate(
            is_favorited=Exists(
                Favorite.objects.filter(
                    recipe__pk=OuterRef('pk'),
                    user_id=user_id,
                )
            ),
            is_in_shopping_cart=Exists(
                ShoppingCart.objects.filter(
                    recipe__pk=OuterRef('pk'),
                    user_id=user_id,
                )
            ),
        )


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Заголовок',
    )
    image = models.ImageField(
        blank=True,
        upload_to='recipes/',
        verbose_name='Изображение',
    )
    text = models.TextField(
        verbose_name='Текст',
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientAmount',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
    )
    cooking_time = models.IntegerField(
        verbose_name='Время готовки',
        help_text='в минутах',
        default=settings.COOKING_TIME_MIN_VALUE,
        validators=[
            validators.MinValueValidator(
                settings.COOKING_TIME_MIN_VALUE,
                message=settings.COOKING_TIME_MIN_ERROR
            ),
        ],
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    objects = RecipeQuerySet.as_manager()

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredients_amount',
        verbose_name='ингрединты в рецептах',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients_amount',
        verbose_name='Рецепт',
    )
    amount = models.IntegerField(
        verbose_name='Количество',
        default=settings.INGREDIENT_MIN_AMOUNT,
        validators=(
            validators.MinValueValidator(
                settings.INGREDIENT_MIN_AMOUNT,
                message='Количество ингредиентов не может быть меньше одного!'
            ),
        ),
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'ингредиенты'
        constraints = [
            models.UniqueConstraint(fields=['recipe', 'ingredient'],
                                    name='unique_ingredient')
        ]

    def __str__(self):
        return f'{self.ingredient}: {self.amount}'


class Favorite(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь добавлен в избранное',
    )

    class Meta:
        default_related_name = 'favorite'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_user_recipe',
            ),
        )


class ShoppingCart(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='default_related_name',
        verbose_name='Добавлено в корзину',
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины пользователей'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe',),
                name='unique_user_shopping',
            ),
        )
