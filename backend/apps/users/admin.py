from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'nombre_completo', 'rol', 'activo', 'fecha_registro')
    list_filter = ('rol', 'activo', 'is_staff', 'fecha_registro')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-fecha_registro',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('rol', 'activo', 'ultimo_acceso')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información Adicional', {
            'fields': ('rol', 'activo')
        }),
    )