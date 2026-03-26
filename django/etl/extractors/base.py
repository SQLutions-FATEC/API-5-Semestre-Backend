import os
import pandas as pd
from etl.utils.logger import get_logger

logger = get_logger(__name__)

#caminho base para os arquivos CSV
CSV_BASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data')


class BaseExtractor:
    """
    Classe base para todos os extractors.
    Cada extractor deve definir:
        - csv_file: nome do arquivo CSV de origem (ex: 'programas.csv')
    """

    csv_file: str = None

    def extract(self) -> pd.DataFrame:
        caminho = os.path.join(CSV_BASE_PATH, self.csv_file)
        try:
            logger.info(f"[{self.__class__.__name__}] Iniciando extração de '{self.csv_file}'...")
            df = pd.read_csv(caminho)
            logger.info(f"[{self.__class__.__name__}] {len(df)} registros extraídos de '{self.csv_file}'.")
            return df
        except FileNotFoundError:
            logger.error(f"[{self.__class__.__name__}] Arquivo não encontrado: {caminho}")
            raise
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Falha na extração de '{self.csv_file}': {e}")
            raise