import logging
from logging.handlers import RotatingFileHandler
import os

class MyLogger:
    """
    Logger personalizado para el proyecto. Puede escribirse a consola y/o archivo.
    """

    def __init__(self, level: str = "INFO", log_file: str = "logs/app.log"):
        # Asegurar que el directorio exista
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        self.logger = logging.getLogger("TriviaApp")
        self.logger.setLevel(level.upper())

        # Evita duplicar handlers si ya está configurado
        if not self.logger.handlers:
            # Consola
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(console_handler)

            # Archivo con rotación
            file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5)
            file_handler.setFormatter(self._get_formatter())
            self.logger.addHandler(file_handler)

    def _get_formatter(self):
        return logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")

    def get_logger(self):
        return self.logger