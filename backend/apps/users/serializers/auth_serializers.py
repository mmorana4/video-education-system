from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.tokens import RefreshToken

Usuario = get_user_model()


class RegistroSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=Usuario.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirmacion = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = Usuario
        fields = (
            'username', 'email', 'password', 'password_confirmacion',
            'first_name', 'last_name', 'rol'
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }
    
    def validate(self, attrs):
        """Validar que las contraseñas coincidan"""
        if attrs['password'] != attrs['password_confirmacion']:
            raise serializers.ValidationError({
                "password": "Las contraseñas no coinciden."
            })
        return attrs
    
    def create(self, validated_data):
        """Crear usuario con contraseña hasheada"""
        validated_data.pop('password_confirmacion')
        
        usuario = Usuario.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            rol=validated_data.get('rol', 'docente'),
            password=validated_data['password']
        )
        
        return usuario


class LoginSerializer(serializers.Serializer):
    """
    Serializer para el login de usuarios
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validar credenciales del usuario"""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            usuario = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            if not usuario:
                raise serializers.ValidationError(
                    'No se pudo iniciar sesión con las credenciales proporcionadas.',
                    code='authorization'
                )
            
            if not usuario.is_active:
                raise serializers.ValidationError(
                    'Esta cuenta está desactivada.',
                    code='authorization'
                )
            
            attrs['usuario'] = usuario
            return attrs
        else:
            raise serializers.ValidationError(
                'Debe incluir "username" y "password".',
                code='authorization'
            )


class UsuarioSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información del usuario
    """
    nombre_completo = serializers.CharField(read_only=True)
    
    class Meta:
        model = Usuario
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'nombre_completo', 'rol', 'activo', 'fecha_registro',
            'ultimo_acceso'
        )
        read_only_fields = ('id', 'fecha_registro', 'ultimo_acceso')


class CambioPasswordSerializer(serializers.Serializer):
    """
    Serializer para cambiar contraseña
    """
    password_actual = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    password_nuevo = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_nuevo_confirmacion = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_password_actual(self, value):
        """Validar que la contraseña actual sea correcta"""
        usuario = self.context['request'].user
        if not usuario.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value
    
    def validate(self, attrs):
        """Validar que las contraseñas nuevas coincidan"""
        if attrs['password_nuevo'] != attrs['password_nuevo_confirmacion']:
            raise serializers.ValidationError({
                "password_nuevo": "Las contraseñas nuevas no coinciden."
            })
        return attrs
    
    def save(self, **kwargs):
        """Guardar la nueva contraseña"""
        usuario = self.context['request'].user
        usuario.set_password(self.validated_data['password_nuevo'])
        usuario.save()
        return usuario


class ActualizarPerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar perfil de usuario
    """
    class Meta:
        model = Usuario
        fields = ('first_name', 'last_name', 'email')
        extra_kwargs = {
            'email': {
                'validators': [UniqueValidator(queryset=Usuario.objects.all())]
            }
        }