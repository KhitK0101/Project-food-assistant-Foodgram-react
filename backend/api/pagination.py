from django.core import paginator
from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    django_paginator_class = paginator.Paginator
    page_size = 6
    page_size_param = 'limit'
