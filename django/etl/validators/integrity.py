from etl.utils.logger import get_logger

logger = get_logger(__name__)


def validate(entidade: str, total_csv: int, total_dw: int):
    """
    Valida se a quantidade de registros extraídos do CSV
    corresponde à quantidade carregada na tabela do DW.
    """
    if total_csv != total_dw:
        msg = (
            f"[{entidade}] FALHA DE INTEGRIDADE: "
            f"csv={total_csv} registros | dw={total_dw} registros"
        )
        logger.error(msg)
        raise ValueError(msg)

    logger.info(f"[{entidade}] Integridade OK — {total_dw} registros conferem.")