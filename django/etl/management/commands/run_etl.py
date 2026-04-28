from django.core.management.base import BaseCommand
from api.models import (
    DimPrograma, DimProjeto, DimTarefa, DimMaterial,
    DimFornecedor, DimSolicitacao, FatoTarefa, FatoEmpenho, FatoCompra,
    DimLocalizacao, FatoEstoqueSaldo
)

from etl.transformations.transformers import standardize_strings, handle_nulls, calculate_project_metrics, calculate_estoque_saldo

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
    EstoqueMateriaisExtractor
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
    load_localizacoes,
    load_fato_estoque_saldo
    )
from etl.validators.integrity import validate
from etl.utils.logger import get_logger

logger = get_logger("etl.command")

SEPARATOR = "=============================="

PIPELINE = [
    #(Extractor, loader_fn, Model_DW, nome_legivel)
    (ProgramasExtractor,        load_programas,    DimPrograma,    "Programas"),
    (ProjetosExtractor,         load_projetos,     DimProjeto,     "Projetos"),
    (TarefasProjetoExtractor,   load_tarefas,      DimTarefa,      "Tarefas"),
    (MateriaisExtractor,        load_materiais,    DimMaterial,    "Materiais"),
    (FornecedoresExtractor,     load_fornecedores, DimFornecedor,  "Fornecedores"),
    (SolicitacoesCompraExtractor, load_solicitacoes, DimSolicitacao, "Solicitações de Compra"),
    (TempoTarefasExtractor,     load_fato_tarefa,  FatoTarefa,     "Fatos de Tarefa"),
    (EmpenhoMateriaisExtractor, load_fato_empenho, FatoEmpenho,    "Fatos de Empenho"),
    (PedidosCompraExtractor,    load_fato_compra,  FatoCompra,     "Fatos de Compra"),
]


class Command(BaseCommand):
    help = "Executa o processo manual do ETL: Extração, Transformação e Carga no DW"

    def handle(self, *args, **kwargs):
        # ... (logs iniciais)
        
        erros = []

        for extractor_class, loader_fn, model_dw, nome in PIPELINE:
            try:
                self.stdout.write(self.style.NOTICE(f"\nProcessando {nome}..."))
                
                # 1. Extração
                self.stdout.write(f" -> Extraindo {nome.lower()}...")
                extractor = extractor_class()
                df = extractor.extract()

                # 2. Transformação
                self.stdout.write(" -> Aplicando transformações de negócio...")
                df = standardize_strings(df, ['status', 'categoria', 'prioridade', 'cidade', 'estado', 'nome', 'responsavel'])
                df = handle_nulls(df)
                
                if nome in ['Projetos', 'Tarefas']:
                    df = calculate_project_metrics(df)

                # 3. Carga
                self.stdout.write(" -> Carregando no Data Warehouse...")
                loader_fn(df)

                #validação de integridade
                total_dw = model_dw.objects.count()
                validate(nome, len(df), total_dw)
                self.stdout.write(self.style.SUCCESS(f" -> {nome} sincronizados com sucesso!"))

            except Exception as e:
                logger.error(f"[{nome}] Falha: {e}")
                self.stdout.write(self.style.ERROR(f" -> Erro ao processar {nome}: {e}"))
                erros.append(nome)

        # --- ESTOQUE / SALDO
        try:
            self.stdout.write(self.style.NOTICE("\nProcessando Estoque e Saldo..."))

            # 1. Extração
            self.stdout.write(" -> Extraindo dados de estoque, solicitações, materiais e pedidos...")
            df_estoque = EstoqueMateriaisExtractor().extract()
            df_solicitacoes = SolicitacoesCompraExtractor().extract()
            df_materiais = MateriaisExtractor().extract()
            df_pedidos = PedidosCompraExtractor().extract()

            # 2. Transformação 
            self.stdout.write(" -> Calculando saldo de estoque...")
            df_estoque_transformado = calculate_estoque_saldo(df_estoque, df_solicitacoes, df_materiais, df_pedidos)

            # 3. Carga
            self.stdout.write(" -> Carregando localizações no Data Warehouse...")
            load_localizacoes(df_estoque_transformado)
            total_loc = DimLocalizacao.objects.count()
            validate("Localizações", len(df_estoque_transformado['localizacao'].unique()), total_loc)
            self.stdout.write(self.style.SUCCESS(f" -> Localizações sincronizadas com sucesso!"))

            self.stdout.write(" -> Carregando saldo de estoque no Data Warehouse...")
            load_fato_estoque_saldo(df_estoque_transformado)
            total_saldo = FatoEstoqueSaldo.objects.count()
            validate("Estoque Saldo", len(df_estoque_transformado), total_saldo)
            self.stdout.write(self.style.SUCCESS(f" -> Estoque Saldo sincronizado com sucesso!"))

        except Exception as e:
            logger.error(f"[Estoque/Saldo] Falha: {e}")
            self.stdout.write(self.style.ERROR(f" -> Erro ao processar Estoque/Saldo: {e}"))
            erros.append("Estoque/Saldo")

        logger.info(SEPARATOR)
        self.stdout.write("\n" + SEPARATOR)
        
        if erros:
            logger.error(f"ETL FINALIZADO COM ERROS: {erros}")
            self.stdout.write(self.style.ERROR(f"Sincronização finalizada com erros: {erros}"))
        else:
            logger.info("ETL FINALIZADO COM SUCESSO")
            self.stdout.write(self.style.SUCCESS("Carga finalizada com sucesso!"))
            
        logger.info(SEPARATOR)
