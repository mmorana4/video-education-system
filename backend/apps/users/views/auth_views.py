from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from datetime import datetime

from apps.users.serializers import (
    RegistroSerializer,
    LoginSerializer,
    UsuarioSerializer,
    CambioPasswordSerializer,
    ActualizarPerfilSerializer
)

Usuario = get_user_model()


class RegistroView(generics.CreateAPIView):
    """
    Vista para registrar nuevos usuarios
    
    POST /api/users/registro/
    """
    queryset = Usuario.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        
        # Generar tokens JWT
        refresh = RefreshToken.for_user(usuario)
        
        # Serializar datos del usuario
        usuario_data = UsuarioSerializer(usuario).data
        
        return Response({
            'usuario': usuario_data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Usuario registrado exitosamente'
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Vista para iniciar sesión
    
    POST /api/users/login/
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer
    
    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        usuario = serializer.validated_data['usuario']
        
        # Actualizar último acceso
        usuario.ultimo_acceso = datetime.now()
        usuario.save(update_fields=['ultimo_acceso'])
        
        # Generar tokens JWT
        refresh = RefreshToken.for_user(usuario)
        
        # Serializar datos del usuario
        usuario_data = UsuarioSerializer(usuario).data
        
        return Response({
            'usuario': usuario_data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Inicio de sesión exitoso'
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    Vista para cerrar sesión (blacklist del refresh token)
    
    POST /api/users/logout/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token es requerido"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                "message": "Sesión cerrada exitosamente"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": "Token inválido o expirado"},
                status=status.HTTP_400_BAD_REQUEST
            )


class PerfilUsuarioView(generics.RetrieveUpdateAPIView):
    """
    Vista para obtener y actualizar perfil del usuario autenticado
    
    GET /api/users/perfil/
    PUT/PATCH /api/users/perfil/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ActualizarPerfilSerializer
        return UsuarioSerializer


class CambioPasswordView(APIView):
    """
    Vista para cambiar contraseña del usuario autenticado
    
    POST /api/users/cambio-password/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CambioPasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            "message": "Contraseña cambiada exitosamente"
        }, status=status.HTTP_200_OK)


class VerificarTokenView(APIView):
    """
    Vista para verificar si un token es válido
    
    POST /api/users/verificar-token/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        usuario_data = UsuarioSerializer(request.user).data
        return Response({
            "valid": True,
            "usuario": usuario_data
        }, status=status.HTTP_200_OK)