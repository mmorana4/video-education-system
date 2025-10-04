from django.core.management.base import BaseCommand
from apps.videos.services.file_cleaner import clean_temp_files


class Command(BaseCommand):
    help = 'Limpia archivos temporales antiguos'
    
    def handle(self, *args, **options):
        self.stdout.write('Iniciando limpieza de archivos temporales...')
        
        result = clean_temp_files()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Limpieza completada:\n"
                f"  - Archivos eliminados: {result['deleted_count']}\n"
                f"  - Espacio liberado: {result['freed_space_mb']} MB"
            )
        )