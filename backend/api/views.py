from django.db.models import BooleanField, Exists, OuterRef, Sum, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from djoser.views import UserViewSet

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientAmount,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeFullSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    ShoppingCartSerializer,
    SubscriptionSerializer,
    SubscriptionUserSerializer,
    TagSerializer,
)


class CustomUserViewSet(UserViewSet):
    """Вьюсет для модели пользователя."""

    queryset = User.objects.all()
    pagination_class = LimitPagination
    permission_classes = [IsAuthorOrReadOnly]

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def subscribe(self, request, **kwargs):
        user = request.user
        author = get_object_or_404(User, id=kwargs['id'])

        if request.method == 'POST':
            serializer = SubscriptionSerializer(
                data={'user': user.id, 'author': author.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            serializer_author = SubscriptionUserSerializer(
                author, context={'request': request}
            )
            return Response(
                serializer_author.data, status=status.HTTP_201_CREATED
            )

        subscription = Subscription.objects.filter(user=user, author=author)
        deleted = subscription.delete()

        if deleted[0]:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'detail': 'Подписка не найдена или уже была удалена.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def subscriptions(self, request):
        subscriptions = User.objects.filter(
            following__user=request.user
        )
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionUserSerializer(
            page, many=True, context={'request': request}
        )
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

    permission_classes = (IsAuthorOrReadOnly, IsAuthenticatedOrReadOnly, )
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = LimitPagination

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.all()

        if user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(Favorite.objects.filter(
                    user=user, recipe__pk=OuterRef('pk'))
                ),
                is_in_shopping_cart=Exists(ShoppingCart.objects.filter(
                    user=user, recipe__pk=OuterRef('pk'))
                )
            )
        else:
            queryset = queryset.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField())
            )
        return queryset

    def get_serializer_class(self):
        if self.action in ('favorite', 'shopping_cart'):
            return RecipeShortSerializer
        elif self.action in ('create', 'partial_update'):
            return RecipeWriteSerializer
        elif self.action == 'retrieve':
            return RecipeFullSerializer
        return RecipeFullSerializer

    def add_to_list(self, request, pk, serializer_class, model):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        data = {
            'user': user.pk,
            'recipe': recipe.pk
        }
        serializer = serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = self.get_serializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from_list(self, request, pk, model, message):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        items_list = model.objects.filter(user=user, recipe=recipe)
        deleted_count, _ = items_list.delete()

        if deleted_count > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'errors': f'Рецепт не добавлен в {message.lower()}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def favorite(self, request, pk):
        return self.add_to_list(request, pk, FavoriteSerializer, Favorite)

    @favorite.mapping.delete
    def unfavorite(self, request, pk):
        message = 'Рецепт успешно удален из избранного'
        return self.remove_from_list(request, pk, Favorite, message)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def shopping_cart(self, request, pk):
        return self.add_to_list(
            request, pk, ShoppingCartSerializer, ShoppingCart
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        message = 'Рецепт успешно удален из корзины'
        return self.remove_from_list(request, pk, ShoppingCart, message)

    def list_shopping_cart(self, ingredients):
        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            shopping_list.append(f'{name} - {amount}, {unit}')

        response = HttpResponse(shopping_list, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_cart.txt"'
        return response

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticatedOrReadOnly]
    )
    def download_shopping_cart(self, request):
        ingredients = IngredientAmount.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount')).order_by(
            'ingredient__name'
        )

        response = self.list_shopping_cart(ingredients)
        return response
