from django.contrib import admin

from .models import Subscription, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id',
                    'email',
                    'username',
                    'first_name',
                    'last_name',
                    'password',
                    'role')
    list_filter = ('username', 'email')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author',)
