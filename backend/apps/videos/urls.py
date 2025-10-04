from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.videos.views import (
    VideoViewSet,
    SegmentoViewSet,
    TranscripcionViewSet,
    ResumenEjecutivoViewSet,
)
from apps.videos.views.task_views import TaskStatusView, TestTaskView

app_name = 'videos'

# Router para ViewSets
router = DefaultRouter()
router.register(r'videos', VideoViewSet, basename='video')
router.register(r'segmentos', SegmentoViewSet, basename='segmento')
router.register(r'transcripciones', TranscripcionViewSet, basename='transcripcion')
router.register(r'resumenes', ResumenEjecutivoViewSet, basename='resumen')

urlpatterns = [
    path('', include(router.urls)),
    
    # Endpoints de tareas
    path('tasks/<str:task_id>/', TaskStatusView.as_view(), name='task-status'),
    path('tasks/test/', TestTaskView.as_view(), name='task-test'),
]