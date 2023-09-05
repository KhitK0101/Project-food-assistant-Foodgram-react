import django_filters
from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
    )
    is_favorited = django_filters.NumberFilter(
        method='get_is_favorited'
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = (
            'tags',
            'author',
            'is_favorited',
            'is_in_shopping_cart'
        )

    def get_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(
                favorite__user=user,
                is_favorited=True,
            )
        return Recipe.objects.all()

    def get_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(
                shopping_cart__user=user,
                is_in_shopping_cart=True,
            )
        return Recipe.objects.all()


class IngredientFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='name',
                                     lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
