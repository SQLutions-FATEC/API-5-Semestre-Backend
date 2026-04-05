from django.core.management.base import BaseCommand
from api.models import (
    DimPrograma, DimProjeto, DimTarefa, DimMaterial,
    DimFornecedor, DimSolicitacao, FatoTarefa, FatoEmpenho, FatoCompra
)
from etl.extractors.extractors import (
    ProgramasExtractor,
    ProjetosExtractor,
    TarefasProjetoExtractor,
    TempoTarefasExtractor,
    MateriaisExtractor,
    FornecedoresExtractor,
    SolicitacoesCompraExtractor,
    PedidosCompraExtractor,
    EmpenhoMateriaisExtractor,
)
from etl.loaders.loader import (
    load_programas,
    load_projetos,
    load_tarefas,
    load_materiais,
    load_fornecedores,
    load_solicitacoes,
    load_fato_tarefa,
    load_fato_empenho,
    load_fato_compra,
)
from etl.validators.integrity import validate
from etl.utils.logger import get_logger


from etl.transformations.transformers import (
    standardize_strings, 
    handle_nulls, 
    calculate_project_metrics
)


logger = get_logger("etl.command")

SEPARATOR = "=============================="

PIPELINE = [
    #(Extractor, loader_fn, Model_DW, nome_legivel)
    (ProgramasExtractor,        load_programas,    DimPrograma,    "DimPrograma"),
    (ProjetosExtractor,         load_projetos,     DimProjeto,     "DimProjeto"),
    (TarefasProjetoExtractor,   load_tarefas,      DimTarefa,      "DimTarefa"),
    (MateriaisExtractor,        load_materiais,    DimMaterial,    "DimMaterial"),
    (FornecedoresExtractor,     load_fornecedores, DimFornecedor,  "DimFornecedor"),
    (SolicitacoesCompraExtractor, load_solicitacoes, DimSolicitacao, "DimSolicitacao"),
    (TempoTarefasExtractor,     load_fato_tarefa,  FatoTarefa,     "FatoTarefa"),
    (EmpenhoMateriaisExtractor, load_fato_empenho, FatoEmpenho,    "FatoEmpenho"),
    (PedidosCompraExtractor,    load_fato_compra,  FatoCompra,     "FatoCompra"),
]


class Command(BaseCommand):
    help = "Executa o processo de extração do ETL: lê CSVs e carrega no DW"

    def handle(self, *args, **kwargs):
        logger.info(SEPARATOR)
        logger.info("PROCESSO DE EXTRAÇÃO ETL INICIADO")
        logger.info(SEPARATOR)

        erros = []

        for extractor_class, loader_fn, model_dw, nome in PIPELINE:
            try:
                #extração
                extractor = extractor_class()
                df = extractor.extract()

                #transformacao
                logger.info(f"[{nome}] Aplicando transformações e limpeza...")

                #padronização de strings e tratamento de nulos geral
                df = standardize_strings(df, ['status', 'categoria', 'prioridade', 'cidade', 'estado'])
                df = handle_nulls(df)

                #calculos especificos para tabelas de Projetos e Tarefas
                if nome in ['DimProjeto', 'DimTarefa']:
                    df = calculate_project_metrics(df)

                #carregamento no DW
                loader_fn(df)

                #validação de integridade
                total_dw = model_dw.objects.count()
                validate(nome, len(df), total_dw)

            except Exception as e:
                logger.error(f"[{nome}] Falha: {e}")
                erros.append(nome)

        logger.info(SEPARATOR)
        if erros:
            logger.error(f"EXTRAÇÃO ETL FINALIZADA COM ERROS: {erros}")
            self.stdout.write(self.style.ERROR(f"Extração finalizada com erros: {erros}"))
        else:
            logger.info("EXTRAÇÃO ETL FINALIZADA COM SUCESSO")
            self.stdout.write(self.style.SUCCESS("Extração finalizada com sucesso."))
        logger.info(SEPARATOR)
