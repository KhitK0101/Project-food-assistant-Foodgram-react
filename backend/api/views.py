from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import (Favorite, Ingredient, IngredientAmount, Recipe,
                            ShoppingCart, Tag)
from rest_framework import mixins, status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription, User

from .filters import RecipeFilter
from .permissions import IsAdmin, IsAdminOrReadOnly
from .serializers import (FavoriteSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeShortSerializer,
                          RecipeWriteSerializer, SetPasswordSerializer,
                          ShoppingCartSerializer, SubscriptionSerializer,
                          SubscriptionUserSerializer, TagSerializer,
                          UserGetSerializer, UserSingUpSerializer)


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """User, subscription and list of subscriptions."""

    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action in ('subscriptions', 'subscribe'):
            return SubscriptionUserSerializer
        if self.action in ('list', 'retrieve', 'me'):
            return UserGetSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserSingUpSerializer

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def set_password(self, request):
        user = request.user
        data = request.data
        serializer = self.get_serializer(user, data=data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(
            {
                'detail': 'Пароль успешно изменён'
            },
            status=status.HTTP_204_NO_CONTENT
        )

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAdminOrReadOnly, IsAdmin]
    )
    def subscribe(self, request, pk):
        user = request.user
        author = get_object_or_404(User, pk=pk)
        data = {
            'user': user.pk,
            'author': author.pk
        }
        serializer = SubscriptionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = self.get_serializer(author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, pk):
        user = request.user
        author = get_object_or_404(User, pk=pk)
        Subscription.objects.filter(user=user, author=author).delete()
        message = {
            'detail': 'Вы успешно отписались'
        }
        return Response(message, status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        subscriptions = User.objects.filter(
            subscribing__user=user
        ).prefetch_related('recipes')
        page = self.paginate_queryset(subscriptions)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для отображения ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для отображения тегов."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для отображения рецептов."""
    permission_classes = [IsAdminOrReadOnly, IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('favorite', 'shopping_cart'):
            return RecipeShortSerializer
        if self.action in ('create', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeSerializer

    def get_queryset(self):
        user_id = self.request.user.pk
        return Recipe.objects.add_user_annotations(user_id).select_related(
            'author'
        ).prefetch_related(
            'ingredients', 'tags'
        )

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAdminOrReadOnly, IsAdmin]
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
        permission_classes=[IsAdminOrReadOnly, IsAdmin]
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

    @action(
        detail=False,
        methods=['GET'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        ingredients = IngredientAmount.objects.filter(
            recipe__carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(ingredient_amount=Sum('amount'))
        shopping_list = ['Список покупок:\n']
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['ingredient_amount']
            shopping_list.append(f'\n{name} - {amount}, {unit}')
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = \
            'attachment; filename="shopping_cart.txt"'
        return response
