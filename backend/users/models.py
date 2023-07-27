from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validate_username


class User(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name',)

    GUEST = 'guest'
    AUTHORIZED = 'authorized'
    ADMIN = 'admin'

    USER_ROLES = [
        (GUEST, 'guest'),
        (AUTHORIZED, 'authorized'),
        (ADMIN, 'admin'),
    ]

    email = models.EmailField(
        max_length=settings.LENGTH_EMAIL,
        blank=False,
        unique=True,
        verbose_name='Электронная почта',
    )
    username = models.CharField(
        validators=(validate_username,),
        max_length=settings.LENGTH_DATA_USER,
        blank=False,
        unique=True,
        null=False,
        verbose_name='Имя пользователя',
    )
    first_name = models.CharField(
        max_length=settings.LENGTH_DATA_USER,
        blank=False,
        verbose_name='Фамилия',
    )
    last_name = models.CharField(
        max_length=settings.LENGTH_DATA_USER,
        blank=False,
        verbose_name='Имя',
    )
    password = models.CharField(
        max_length=settings.LENGTH_DATA_USER,
        verbose_name='Пароль',
    )

    class Meta:
        ordering = ('username', 'last_name', 'first_name')
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор рецепта',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['user']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscribition_model'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F("author")),
                name="prevent_self_subscription",
            ),
        ]

    def __str__(self):
        return f'{self.user} subscribed on {self.author}'
