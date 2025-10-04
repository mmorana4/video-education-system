from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class RegistroTestCase(TestCase):
    """Tests para el registro de usuarios"""
    
    def setUp(self):
        self.client = APIClient()
        self.registro_url = reverse('users:registro')
        
        self.datos_validos = {
            'username': 'nuevouser',
            'email': 'nuevo@test.com',
            'password': 'TestPassword123!',
            'password_confirmacion': 'TestPassword123!',
            'first_name': 'Nuevo',
            'last_name': 'Usuario',
            'rol': 'docente'
        }
    
    def test_registro_exitoso(self):
        """Test de registro exitoso de usuario"""
        response = self.client.post(
            self.registro_url,
            self.datos_validos,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('usuario', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        
        # Verificar que el usuario fue creado
        self.assertTrue(
            Usuario.objects.filter(username='nuevouser').exists()
        )
    
    def test_registro_passwords_no_coinciden(self):
        """Test cuando las contraseñas no coinciden"""
        datos = self.datos_validos.copy()
        datos['password_confirmacion'] = 'OtraPassword123!'
        
        response = self.client.post(
            self.registro_url,
            datos,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_registro_email_duplicado(self):
        """Test cuando el email ya está registrado"""
        # Crear usuario existente
        Usuario.objects.create_user(
            username='existente',
            email='nuevo@test.com',
            password='TestPass123!'
        )
        
        response = self.client.post(
            self.registro_url,
            self.datos_validos,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTestCase(TestCase):
    """Tests para el inicio de sesión"""
    
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('users:login')
        
        # Crear usuario de prueba
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            rol='docente'
        )
    
    def test_login_exitoso(self):
        """Test de login exitoso"""
        datos = {
            'username': 'testuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(
            self.login_url,
            datos,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('usuario', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['usuario']['username'], 'testuser')
    
    def test_login_credenciales_invalidas(self):
        """Test con credenciales inválidas"""
        datos = {
            'username': 'testuser',
            'password': 'PasswordIncorrecta'
        }
        
        response = self.client.post(
            self.login_url,
            datos,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_usuario_inactivo(self):
        """Test con usuario inactivo"""
        self.usuario.is_active = False
        self.usuario.save()
        
        datos = {
            'username': 'testuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(
            self.login_url,
            datos,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PerfilTestCase(TestCase):
    """Tests para el perfil de usuario"""
    
    def setUp(self):
        self.client = APIClient()
        self.perfil_url = reverse('users:perfil')
        
        # Crear usuario y autenticar
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User',
            rol='docente'
        )
        
        # Obtener token
        login_url = reverse('users:login')
        response = self.client.post(
            login_url,
            {'username': 'testuser', 'password': 'TestPassword123!'},
            format='json'
        )
        self.token = response.data['tokens']['access']
    
    def test_obtener_perfil_autenticado(self):
        """Test obtener perfil con autenticación"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(self.perfil_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@test.com')
    
    def test_obtener_perfil_sin_autenticacion(self):
        """Test obtener perfil sin autenticación"""
        response = self.client.get(self.perfil_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_actualizar_perfil(self):
        """Test actualizar datos del perfil"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        datos = {
            'first_name': 'NuevoNombre',
            'last_name': 'NuevoApellido',
            'email': 'nuevoemail@test.com'
        }
        
        response = self.client.patch(
            self.perfil_url,
            datos,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, 'NuevoNombre')


class CambioPasswordTestCase(TestCase):
    """Tests para cambio de contraseña"""
    
    def setUp(self):
        self.client = APIClient()
        self.cambio_password_url = reverse('users:cambio_password')
        
        # Crear usuario y autenticar
        self.usuario = Usuario.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )
        
        # Obtener token
        login_url = reverse('users:login')
        response = self.client.post(
            login_url,
            {'username': 'testuser', 'password': 'TestPassword123!'},
            format='json'
        )
        self.token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_cambio_password_exitoso(self):
        """Test cambio de contraseña exitoso"""
        datos = {
            'password_actual': 'TestPassword123!',
            'password_nuevo': 'NuevaPassword456!',
            'password_nuevo_confirmacion': 'NuevaPassword456!'
        }
        
        response = self.client.post(
            self.cambio_password_url,
            datos,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que la nueva contraseña funciona
        self.usuario.refresh_from_db()
        self.assertTrue(
            self.usuario.check_password('NuevaPassword456!')
        )
    
    def test_cambio_password_actual_incorrecta(self):
        """Test con contraseña actual incorrecta"""
        datos = {
            'password_actual': 'PasswordIncorrecta',
            'password_nuevo': 'NuevaPassword456!',
            'password_nuevo_confirmacion': 'NuevaPassword456!'
        }
        
        response = self.client.post(
            self.cambio_password_url,
            datos,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)