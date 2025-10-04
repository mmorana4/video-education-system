import os
import time
from pathlib import Path
from datetime import datetime, timedelta
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class FileCleaner:
    """
    Servicio para limpiar archivos temporales antiguos
    """
    
    def __init__(self):
        self.temp_dir = settings.TEMP_ROOT
        self.lifetime_hours = settings.TEMP_FILE_LIFETIME_HOURS
    
    def clean_old_files(self) -> dict:
        """
        Eliminar archivos temporales más antiguos que el lifetime configurado
        
        Returns:
            dict: Estadísticas de limpieza
        """
        if not self.temp_dir.exists():
            return {'deleted_count': 0, 'freed_space_mb': 0}
        
        try:
            deleted_count = 0
            freed_space = 0
            cutoff_time = time.time() - (self.lifetime_hours * 3600)
            
            for file_path in self.temp_dir.iterdir():
                if file_path.is_file():
                    # Verificar antigüedad
                    file_age = file_path.stat().st_mtime
                    
                    if file_age < cutoff_time:
                        # Obtener tamaño antes de eliminar
                        file_size = file_path.stat().st_size
                        
                        # Eliminar archivo
                        file_path.unlink()
                        
                        deleted_count += 1
                        freed_space += file_size
                        
                        logger.info(f"Eliminado archivo temporal: {file_path.name}")
            
            freed_space_mb = round(freed_space / (1024 * 1024), 2)
            
            logger.info(
                f"Limpieza completada: {deleted_count} archivos, "
                f"{freed_space_mb} MB liberados"
            )
            
            return {
                'deleted_count': deleted_count,
                'freed_space_mb': freed_space_mb
            }
        
        except Exception as e:
            logger.error(f"Error en limpieza de archivos: {str(e)}")
            return {'deleted_count': 0, 'freed_space_mb': 0, 'error': str(e)}
    
    def clean_file(self, file_path: Path) -> bool:
        """
        Eliminar un archivo específico
        
        Args:
            file_path: Ruta del archivo a eliminar
        
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
                logger.info(f"Archivo eliminado: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error al eliminar archivo {file_path}: {str(e)}")
            return False
    
    def get_temp_dir_size(self) -> float:
        """
        Obtener tamaño total de la carpeta temporal
        
        Returns:
            float: Tamaño en MB
        """
        if not self.temp_dir.exists():
            return 0.0
        
        total_size = sum(
            f.stat().st_size for f in self.temp_dir.rglob('*') if f.is_file()
        )
        
        return round(total_size / (1024 * 1024), 2)


def clean_temp_files() -> dict:
    """
    Función helper para limpiar archivos temporales
    
    Returns:
        dict: Estadísticas de limpieza
    """
    cleaner = FileCleaner()
    return cleaner.clean_old_files()