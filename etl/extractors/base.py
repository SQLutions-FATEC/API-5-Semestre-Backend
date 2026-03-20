from django.db import connections, OperationalError
from apps.etl.utils.logger import get_logger

logger = get_logger(__name__)


class BaseExtractor:
    """
Classe base para todos os extratores.

Cada extrator deve definir:

- source_table: nome da tabela operacional da qual extrair os dados
- source_db: alias do banco de dados definido nas configurações do Django (padrão: 'default')
    """

    source_table: str = None
    source_db: str = "default"

    def check_connection(self):
        try:
            connections[self.source_db].ensure_connection()
            logger.info(f"[{self.__class__.__name__}] Connection established with '{self.source_db}'.")
        except OperationalError as e:
            logger.error(f"[{self.__class__.__name__}] Failed to connect to '{self.source_db}': {e}")
            raise

    def extract(self) -> list[dict]:
        self.check_connection()
        try:
            logger.info(f"[{self.__class__.__name__}] Starting extraction from '{self.source_table}'...")
            with connections[self.source_db].cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.source_table}")
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                data = [dict(zip(columns, row)) for row in rows]
            logger.info(f"[{self.__class__.__name__}] Extracted {len(data)} records from '{self.source_table}'.")
            return data
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Extraction failed: {e}")
            raise