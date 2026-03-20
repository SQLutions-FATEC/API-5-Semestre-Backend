from apps.etl.extractors.base import BaseExtractor


class ProgramasEmpresaExtractor(BaseExtractor):
    source_table = "programasempresa"


class ProjetosProgramasExtractor(BaseExtractor):
    source_table = "projetosprogramas"


class TarefasProjetoExtractor(BaseExtractor):
    source_table = "tarefasprojeto"


class TempoTarefasExtractor(BaseExtractor):
    source_table = "tempotarefas"


class MateriaisEngenhariaExtractor(BaseExtractor):
    source_table = "materiaisengenharia"


class FornecedoresExtractor(BaseExtractor):
    source_table = "fornecedor"


class SolicitacoesCompraExtractor(BaseExtractor):
    source_table = "solicitacoescompra"


class PedidosCompraExtractor(BaseExtractor):
    source_table = "pedidoscompra"


class EmpenhoMateriaisExtractor(BaseExtractor):
    source_table = "empenhomateriais"


class ComprasProjetoExtractor(BaseExtractor):
    source_table = "comprasprojeto"


class EstoqueMateriaisExtractor(BaseExtractor):
    source_table = "estoquemateriaisproj"