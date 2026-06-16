import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

class MyLogger:
    """
    Clase personalizada para gestionar logs en la aplicación.
    
    Implementa un singleton para asegurar que solo exista una instancia
    de configuración de logging en toda la aplicación.
    """
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MyLogger, cls).__new__(cls)
            cls._instance._initialize_logging()
        return cls._instance
    
    def _initialize_logging(self):
        """Configura el sistema de logging."""
        # Configurar nivel de log global
        logging.basicConfig(
            level=logging.DEBUG,  # Cambiar a DEBUG para ver más información
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True  # Forzar la configuración
        )
        
        # Directorio para logs
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Configurar formato común
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s:%(lineno)d) - %(message)s'
        )
        
        # Handler para consola con colores
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)  # Nivel para consola
        
        # Handler para archivo con rotación
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'trivia_api.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)  # Nivel para archivo
        
        # Configurar el logger raíz
        root_logger = logging.getLogger()
        # Limpiar handlers existentes
        if root_logger.handlers:
            root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Obtiene un logger con el nombre especificado.
        
        Args:
            name (str, optional): Nombre para el logger.
                                
        Returns:
            logging.Logger: Logger configurado con el nombre especificado.
        """
        if name is None:
            name = "sorteo_api"
        elif not name.startswith("sorteo_api"):
            name = f"sorteo_api.{name}"
            
        # Verificar si ya tenemos este logger en caché
        if name in self._loggers:
            return self._loggers[name]
            
        # Crear y configurar el logger
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)  # Asegurar que el logger específico tiene el nivel correcto
        
        self._loggers[name] = logger
        
        return logger