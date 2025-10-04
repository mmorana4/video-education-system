from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.users.views.auth_views import (
    RegistroView, LoginView, LogoutView, 
    PerfilUsuarioView, CambioPasswordView, VerificarTokenView
    )


app_name = 'users'

urlpatterns = [
    # Autenticación
    path('registro/', RegistroView.as_view(), name='registro'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Perfil de usuario
    path('perfil/', PerfilUsuarioView.as_view(), name='perfil'),
    path('cambio-password/', CambioPasswordView.as_view(), name='cambio_password'),
    path('verificar-token/', VerificarTokenView.as_view(), name='verificar_token'),
]