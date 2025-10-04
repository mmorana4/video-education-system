from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from celery.result import AsyncResult
from apps.videos.tasks import test_task


class TaskStatusView(APIView):
    """
    Vista para obtener estado de una tarea
    GET /api/videos/tasks/{task_id}/
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, task_id):
        """Obtener estado de una tarea por ID"""
        try:
            result = AsyncResult(task_id)
            
            response_data = {
                'task_id': task_id,
                'status': result.status,
                'ready': result.ready(),
                'successful': result.successful() if result.ready() else None,
            }
            
            if result.ready():
                if result.successful():
                    response_data['result'] = result.result
                else:
                    response_data['error'] = str(result.result)
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': f'Error al obtener estado de tarea: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TestTaskView(APIView):
    """
    Vista para ejecutar tarea de prueba
    POST /api/videos/tasks/test/
    """ 
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Ejecutar tarea de prueba"""
        seconds = request.data.get('seconds', 5)
        
        try:
            task = test_task.delay(seconds)
            
            return Response({
                'message': 'Tarea de prueba iniciada',
                'task_id': task.id,
                'seconds': seconds
            }, status=status.HTTP_202_ACCEPTED)
        
        except Exception as e:
            return Response(
                {'error': f'Error al iniciar tarea: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )