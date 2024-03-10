from rest_framework import permissions

class IsSuperOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow superusers to edit
    """

    def has_object_permission(self, request, view, obj):
        # GET, HEAD, OPTION requests are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to superusers
        #return not super().has_object_permission(request, view, obj)
        return request.user.is_superuser