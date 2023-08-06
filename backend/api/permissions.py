from rest_framework.permissions import BasePermission


class IsAuthenticated:
    def has_permission(self, request, view):
        return (
            request.method in ('GET')
            or (request.user.is_authenticated)
        )


class IsAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.method in ('GET')
            or obj.author == request.user
        )
