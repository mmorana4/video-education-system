from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    """
    Modelo de usuario personalizado extendiendo AbstractUser
    """
    ROL_CHOICES = [
        ('docente', 'Docente'),
        ('admin', 'Administrador'),
        ('estudiante', 'Estudiante'),
    ]
    
    email = models.EmailField(
        'Correo Electrónico',
        unique=True,
        error_messages={
            'unique': 'Ya existe un usuario con este correo electrónico.',
        }
    )
    rol = models.CharField(
        'Rol',
        max_length=20,
        choices=ROL_CHOICES,
        default='docente'
    )
    activo = models.BooleanField(
        'Activo',
        default=True
    )
    fecha_registro = models.DateTimeField(
        'Fecha de Registro',
        auto_now_add=True
    )
    ultimo_acceso = models.DateTimeField(
        'Último Acceso',
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def nombre_completo(self):
        return f"{self.first_name} {self.last_name}".strip()