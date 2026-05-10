from etl.extractors.base import BaseExtractor


class ProgramasExtractor(BaseExtractor):
    csv_file = 'programas.csv'


class ProjetosExtractor(BaseExtractor):
    csv_file = 'projetos.csv'


class TarefasProjetoExtractor(BaseExtractor):
    csv_file = 'tarefas_projeto.csv'


class TempoTarefasExtractor(BaseExtractor):
    csv_file = 'tempo_tarefas.csv'


class MateriaisExtractor(BaseExtractor):
    csv_file = 'materiais.csv'


class FornecedoresExtractor(BaseExtractor):
    csv_file = 'fornecedores.csv'


class SolicitacoesCompraExtractor(BaseExtractor):
    csv_file = 'solicitacoes_compra.csv'


class PedidosCompraExtractor(BaseExtractor):
    csv_file = 'pedidos_compra.csv'


class EmpenhoMateriaisExtractor(BaseExtractor):
    csv_file = 'empenho_materiais.csv'


class ComprasProjetoExtractor(BaseExtractor):
    csv_file = 'compras_projeto.csv'


class EstoqueMateriaisExtractor(BaseExtractor):
    csv_file = 'estoque_materiais_projeto.csv'