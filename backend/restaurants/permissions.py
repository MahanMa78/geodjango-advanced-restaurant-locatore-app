from rest_framework import permissions

class IsRestaurantOwnerOrAdmin(permissions.BasePermission):
    """
   It allows only the system administrator (ADMIN)
   or the restaurant owner (RESTAURANT_OWNER) to edit or delete restaurant data.
    """

    def has_permission(self, request, view):
        # Read requests (GET, HEAD, OPTIONS) are open to everyone.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For creating/editing/deleting, the user must be logged in and have the role of restaurant owner or admin
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['RESTAURANT_OWNER', 'ADMIN']
        )

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # The system administrator has access to everything.
        if request.user.role == 'ADMIN':
            return True
        
        # A restaurant manager can only edit the restaurant they own.
        return obj.owner == request.user