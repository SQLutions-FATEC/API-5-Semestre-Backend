from apps.etl.utils.logger import get_logger

logger = get_logger(__name__)


def validate(extractor_name: str, source_count: int, stage_count: int):
    """
    Valida se a quantidade de registros extraídos da origem
    corresponde à quantidade carregada na tabela de stage.
    """
    if source_count != stage_count:
        msg = (
            f"[{extractor_name}] FALHA DE INTEGRIDADE: "
            f"origem={source_count} registros | stage={stage_count} registros"
        )
        logger.error(msg)
        raise ValueError(msg)

    logger.info(f"[{extractor_name}] Integridade OK — {stage_count} registros conferem.")