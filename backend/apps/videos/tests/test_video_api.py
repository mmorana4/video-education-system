from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.videos.models import Video, Segmento

Usuario = get_user_model()


class VideoAPITestCase(TestCase):
    """Tests para API de videos"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Crear usuario y autenticar
        self.usuario = Usuario.objects.create_user(
            username='testdocente',
            email='test@test.com',
            password='TestPassword123!',
            rol='docente'
        )
        
        # Obtener token
        login_url = reverse('users:login')
        response = self.client.post(
            login_url,
            {'username': 'testdocente', 'password': 'TestPassword123!'},
            format='json'
        )
        self.token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Crear video de prueba
        self.video = Video.objects.create(
            usuario=self.usuario,
            titulo='Video de Prueba',
            fuente='youtube',
            url_original='https://youtube.com/watch?v=test',
            duracion_segundos=3600,
            estado='completado'
        )
    
    def test_listar_videos(self):
        """Test listar videos del usuario"""
        url = reverse('videos:video-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['titulo'], 'Video de Prueba')
    
    def test_crear_video(self):
        """Test crear nuevo video"""
        url = reverse('videos:video-list')
        data = {
            'titulo': 'Nuevo Video',
            'fuente': 'youtube',
            'url_original': 'https://youtube.com/watch?v=nuevo'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Video.objects.count(), 2)
        self.assertEqual(response.data['titulo'], 'Nuevo Video')
    
    def test_obtener_video_detalle(self):
        """Test obtener detalle de un video"""
        url = reverse('videos:video-detail', args=[self.video.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.video.id)
        self.assertEqual(response.data['titulo'], 'Video de Prueba')
    
    def test_actualizar_video(self):
        """Test actualizar video"""
        url = reverse('videos:video-detail', args=[self.video.id])
        data = {'titulo': 'Video Actualizado'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.video.refresh_from_db()
        self.assertEqual(self.video.titulo, 'Video Actualizado')
    
    def test_eliminar_video(self):
        """Test eliminar video"""
        url = reverse('videos:video-detail', args=[self.video.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Video.objects.count(), 0)
    
    def test_buscar_videos(self):
        """Test buscar videos por título"""
        url = reverse('videos:video-list')
        response = self.client.get(url, {'search': 'Prueba'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_filtrar_por_estado(self):
        """Test filtrar videos por estado"""
        url = reverse('videos:video-list')
        response = self.client.get(url, {'estado': 'completado'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_estadisticas_videos(self):
        """Test obtener estadísticas"""
        url = reverse('videos:video-estadisticas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_videos', response.data)
        self.assertEqual(response.data['total_videos'], 1)
    
    def test_obtener_segmentos_de_video(self):
        """Test obtener segmentos de un video"""
        # Crear segmento
        Segmento.objects.create(
            video=self.video,
            titulo='Segmento 1',
            descripcion='Descripción',
            timestamp_inicio_seg=0,
            timestamp_fin_seg=300,
            duracion_seg=300,
            orden=1,
            relevancia_score=8.5
        )
        
        url = reverse('videos:video-segmentos', args=[self.video.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['titulo'], 'Segmento 1')


class SegmentoAPITestCase(TestCase):
    """Tests para API de segmentos"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Crear usuario y autenticar
        self.usuario = Usuario.objects.create_user(
            username='testdocente',
            email='test@test.com',
            password='TestPassword123!',
            rol='docente'
        )
        
        # Obtener token
        login_url = reverse('users:login')
        response = self.client.post(
            login_url,
            {'username': 'testdocente', 'password': 'TestPassword123!'},
            format='json'
        )
        self.token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        # Crear video
        self.video = Video.objects.create(
            usuario=self.usuario,
            titulo='Video de Prueba',
            fuente='youtube',
            duracion_segundos=3600,
            estado='completado'
        )
        
        # Crear segmento
        self.segmento = Segmento.objects.create(
            video=self.video,
            titulo='Segmento 1',
            descripcion='Descripción del segmento',
            timestamp_inicio_seg=0,
            timestamp_fin_seg=300,
            duracion_seg=300,
            orden=1,
            relevancia_score=8.5,
            tipo_contenido='introduccion'
        )
    
    def test_listar_segmentos(self):
        """Test listar segmentos"""
        url = reverse('videos:segmento-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_crear_segmento(self):
        """Test crear nuevo segmento"""
        url = reverse('videos:segmento-list')
        data = {
            'video': self.video.id,
            'titulo': 'Nuevo Segmento',
            'descripcion': 'Descripción',
            'timestamp_inicio_seg': 300,
            'timestamp_fin_seg': 600,
            'orden': 2,
            'relevancia_score': 7.5,
            'tipo_contenido': 'concepto_clave'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Segmento.objects.count(), 2)
    
    def test_crear_segmento_timestamps_invalidos(self):
        """Test crear segmento con timestamps inválidos"""
        url = reverse('videos:segmento-list')
        data = {
            'video': self.video.id,
            'titulo': 'Segmento Inválido',
            'descripcion': 'Descripción',
            'timestamp_inicio_seg': 600,
            'timestamp_fin_seg': 300,  # Menor al inicio
            'orden': 2,
            'relevancia_score': 7.5,
            'tipo_contenido': 'concepto_clave'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_segmentos_mas_relevantes(self):
        """Test obtener segmentos más relevantes"""
        url = reverse('videos:segmento-mas-relevantes')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)


class PermisosPropietarioTestCase(TestCase):
    """Tests para permisos de propietario"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Crear dos usuarios
        self.usuario1 = Usuario.objects.create_user(
            username='docente1',
            email='docente1@test.com',
            password='TestPassword123!',
            rol='docente'
        )
        
        self.usuario2 = Usuario.objects.create_user(
            username='docente2',
            email='docente2@test.com',
            password='TestPassword123!',
            rol='docente'
        )
        
        # Video del usuario1
        self.video = Video.objects.create(
            usuario=self.usuario1,
            titulo='Video de Usuario 1',
            fuente='youtube',
            estado='completado'
        )
        
        # Autenticar como usuario2
        login_url = reverse('users:login')
        response = self.client.post(
            login_url,
            {'username': 'docente2', 'password': 'TestPassword123!'},
            format='json'
        )
        self.token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_usuario_no_puede_ver_videos_de_otro(self):
        """Test que un usuario no ve videos de otro usuario"""
        url = reverse('videos:video-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_usuario_no_puede_actualizar_video_de_otro(self):
        """Test que un usuario no puede actualizar video de otro"""
        url = reverse('videos:video-detail', args=[self.video.id])
        data = {'titulo': 'Intento de actualización'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_usuario_no_puede_eliminar_video_de_otro(self):
        """Test que un usuario no puede eliminar video de otro"""
        url = reverse('videos:video-detail', args=[self.video.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)