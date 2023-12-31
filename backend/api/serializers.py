from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.fields import HiddenField
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientAmount,
    Recipe,
    ShoppingCart,
    Tag,
)
from users.models import Subscription, User


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserGetSerializer(serializers.ModelSerializer):
    """Сериализатор для всех пользователей."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username',
            'first_name', 'last_name', 'is_subscribed'
        )

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and request.user.follower.filter(author=author).exists())


class SubscriptionUserSerializer(serializers.ModelSerializer):
    """Сериализатор подписки пользователя."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        recipes = obj.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        serializer = RecipeShortSerializer(
            recipes, many=True, read_only=True
        )
        return serializer.data

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and request.user.follower.filter(author=obj).exists())


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор модели подписки."""

    class Meta:
        model = Subscription
        fields = ('user', 'author')
        validators = [
            UniqueTogetherValidator(
                queryset=Subscription.objects.all(),
                fields=('user', 'author'),
                message='Вы уже подписаны на этого пользователя'
            )
        ]

    def validate(self, data):
        if data['user'] == data['author']:
            raise serializers.ValidationError(
                'Нельзя подписываться на самого себя!'
            )
        return data


class IngredientSerializer(serializers.ModelSerializer):
    """Список ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    """Список тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиента в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )

    class Meta:
        model = IngredientAmount
        fields = ('id', 'name', 'measurement_unit', 'amount')


class AddIngredientToRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(write_only=True,
                                      min_value=1, max_value=32000)

    class Meta:
        model = IngredientAmount
        fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор модели рецепта (создания рецепта)."""

    image = Base64ImageField()
    author = HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = AddIngredientToRecipeSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'image', 'tags', 'author', 'ingredients',
            'name', 'text', 'cooking_time'
        )

    def create_bulk_ingredients(self, recipe, ingredients):
        ingredients_all = []
        for ingredient in ingredients:
            new_ingredient = IngredientAmount(
                recipe=recipe, ingredient=ingredient.get('id'),
                amount=ingredient.get('amount')
            )
            ingredients_all.append(new_ingredient)
        IngredientAmount.objects.bulk_create(ingredients_all)

    @transaction.atomic
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self.create_bulk_ingredients(recipe, ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.tags.clear()
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.create_bulk_ingredients(recipe=instance,
                                     ingredients=ingredients)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        queryset = Recipe.objects.add_user_annotations(
            self.context['request'].user.id
        )
        recipe = get_object_or_404(queryset, id=instance.id)

        return RecipeFullSerializer(
            recipe, context={'request': self.context.get('request')}
        ).data

    def validate(self, data):
        cooking_time = data.get('cooking_time')
        if cooking_time <= 0:
            raise serializers.ValidationError(
                {
                    'error': 'Время приготовления не может быть меньше минуты'
                }
            )
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                'Нужно указать хотя бы 1 тег.'
            )
        tags_set = set(tags)
        if len(tags) != len(tags_set):
            raise serializers.ValidationError(
                'Такой тег уже существует, добавьте новый!'
            )

        ingredients_list = data.get('ingredients', [])
        if len(ingredients_list) < 1:
            raise serializers.ValidationError({
                'error': 'Список ингредиентов не должен быть пустым'
            })

        ingredient_ids = [ingredient['id'] for ingredient in ingredients_list]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                {'error': 'Ингредиенты не должны повторяться'}
            )
        return data


class RecipeFullSerializer(serializers.ModelSerializer):
    """Сериализатор модели Recipe для GET-запросов."""

    image = Base64ImageField()
    tags = TagSerializer(many=True)
    author = UserGetSerializer(read_only=True)
    ingredients = IngredientAmountSerializer(
        source='ingredients_amount', many=True
    )
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'cooking_time', 'tags',
            'author', 'ingredients', 'text', 'is_favorited',
            'is_in_shopping_cart'
        )


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор добавления рецептов в избранное."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Вы уже добавили рецепт в избранное'
            )
        ]


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор добавления рецептов в список покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Вы уже добавили рецепт в корзину'
            )
        ]
