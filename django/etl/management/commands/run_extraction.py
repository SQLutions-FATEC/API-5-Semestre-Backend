from django.core.management.base import BaseCommand

from etl.extractors.extractors import(
    ProgramasEmpresaExtractor,
    ProjetosProgramasExtractor,
    TarefasProjetoExtractor,
    TempoTarefasExtractor,
    MateriaisEngenhariaExtractor,
    FornecedoresExtractor,
    SolicitacoesCompraExtractor,
    PedidosCompraExtractor,
    EmpenhoMateriaisExtractor,
    ComprasProjetoExtractor,
    EstoqueMateriaisExtractor,
)
from etl.stage.loader import load_to_stage
from etl.validators.integrity import validate
from etl.utils.logger import get_logger

logger = get_logger("etl.command")

EXTRACTORS = [
    ProgramasEmpresaExtractor,
    ProjetosProgramasExtractor,
    TarefasProjetoExtractor,
    TempoTarefasExtractor,
    MateriaisEngenhariaExtractor,
    FornecedoresExtractor,
    SolicitacoesCompraExtractor,
    PedidosCompraExtractor,
    EmpenhoMateriaisExtractor,
    ComprasProjetoExtractor,
    EstoqueMateriaisExtractor,
]


class Command(BaseCommand):
    help = "Executa o processo de extração do ETL para todas as tabelas operacionais"

    def handle(self, *args, **kwargs):
        logger.info("==============================")
        logger.info("PROCESSO DE EXTRAÇÃO ETL INICIADO")
        logger.info("==============================")

        errors = []

        for ExtractorClass in EXTRACTORS:
            name = ExtractorClass.__name__
            try:
                extractor = ExtractorClass()
                data = extractor.extract()
                stage_count = load_to_stage(name, data)
                validate(name, len(data), stage_count)
            except Exception as e:
                logger.error(f"[{name}] Falha: {e}")
                errors.append(name)

        logger.info("==============================")
        if errors:
            logger.error(f"EXTRAÇÃO ETL FINALIZADA COM ERROS: {errors}")
            self.stdout.write(self.style.ERROR(f"Extração finalizada com erros: {errors}"))
        else:
            logger.info("EXTRAÇÃO ETL FINALIZADA COM SUCESSO")
            self.stdout.write(self.style.SUCCESS("Extração finalizada com sucesso."))
        logger.info("==============================")