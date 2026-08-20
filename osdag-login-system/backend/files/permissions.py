from rest_framework import permissions
from .models import FileAccess


class IsOwnerOrHasAccess(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user:
            return True
        if request.method not in permissions.SAFE_METHODS:
            return False
        grant = FileAccess.objects.filter(file=obj, shared_with=request.user).first()
        if grant and not grant.is_expired:
            return True
        return False


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsTeamCreatorOrMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.created_by == request.user:
            return True
        return obj.members.filter(id=request.user.id).exists()
