from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    page_size = settings.PAGINATION_PAGE_SIZE
    page_size_query_param = 'limit'
