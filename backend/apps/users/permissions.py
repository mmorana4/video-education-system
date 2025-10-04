from rest_framework import permissions


class IsDocente(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a docentes
    """
    message = 'Solo los docentes pueden acceder a este recurso.'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.rol == 'docente'


class IsAdmin(permissions.BasePermission):
    """
    Permiso personalizado para permitir solo a administradores
    """
    message = 'Solo los administradores pueden acceder a este recurso.'
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.rol == 'admin'


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permiso personalizado para permitir acceso al propietario o admin
    """
    message = 'Solo el propietario o un administrador pueden acceder a este recurso.'
    
    def has_object_permission(self, request, view, obj):
        # Admin tiene acceso total
        if request.user.rol == 'admin':
            return True
        
        # Verificar si el objeto tiene un campo 'usuario'
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        
        # Verificar si el objeto es el propio usuario
        return obj == request.user


class IsDocenteOrAdmin(permissions.BasePermission):
    """
    Permiso para docentes y administradores
    """
    message = 'Solo los docentes y administradores pueden acceder a este recurso.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.rol in ['docente', 'admin']
        )