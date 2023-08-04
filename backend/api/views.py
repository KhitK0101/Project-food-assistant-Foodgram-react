from django.db.models import Sum
from djoser.views import UserViewSet
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, IngredientAmount, Recipe,
                            ShoppingCart, Tag)
from rest_framework import status, viewsets, permissions, response
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import RecipeFilter, IngredientFilter
from .pagination import LimitPagination
from .permissions import IsAuthorOrReadOnly, IsAuthenticated
from .serializers import (
    FavoriteSerializer, IngredientSerializer,
    RecipeShortSerializer, RecipeWriteSerializer,
    ShoppingCartSerializer,
    SubscriptionUserSerializer, TagSerializer,
)
from users.models import Subscription, User


class CustomUserViewSet(UserViewSet):
    """Вьюсет для модели пользователя."""

    queryset = User.objects.all()
    pagination_class = LimitPagination
    permission_classes = [IsAuthorOrReadOnly]

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author = get_object_or_404(User, id=kwargs['pk'])
        if request.method == 'POST':
            serializer = SubscriptionUserSerializer(
                author,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            Subscription.objects.create(user=user, author=author)
            return response.Response(serializer.data,
                                     status=status.HTTP_201_CREATED)
        if request.method == 'DELETE':
            get_object_or_404(
                Subscription, user=user.id, author=author
            ).delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = Subscription.objects.filter(
            user=user.id
        ).prefetch_related('recipes')
        page = self.paginate_queryset(subscriptions)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для отображения ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для отображения тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для отображения рецептов."""
    permission_classes = [IsAuthorOrReadOnly, IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    queryset = Recipe.objects.all()

    def get_serializer_class(self):
        if self in ('favorite', 'shopping_cart'):
            return RecipeShortSerializer
        elif self in ('create', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeShortSerializer

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthorOrReadOnly, IsAuthenticated]
    )
    def favorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': user.pk,
            'recipe': recipe.pk
        }
        serializer = FavoriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def unfavorite(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        Favorite.objects.filter(user=user, recipe=recipe).delete()
        message = {
            'detail': 'Рецепт успешно удален из избранного'
        }
        return Response(message, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': user.pk,
            'recipe': recipe.pk
        }
        serializer = ShoppingCartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
        message = {
            'detail':
                'Вы успешно удалили рецепт из корзины'
        }
        return Response(message, status=status.HTTP_204_NO_CONTENT)

    def list_shopping_cart(self, request):
        ingredients = IngredientAmount.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount')
                   ).values_list(
            'ingredient__name', 'total_amount',
            'ingredient__measurement_unit',
        )
        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            shopping_list.append(f'\n{name} - {amount}, {unit}')
        return shopping_list

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        response = HttpResponse(
            RecipeViewSet.list_shopping_cart, content_type='text/plain',
        )
        response['Content-Disposition'] = \
            'attachment; filename="shopping_list.txt"'
        return response
#   Здесь осталась ошибка как мне сказали в 181 строке но как это
#   исправить я так и не понял.
