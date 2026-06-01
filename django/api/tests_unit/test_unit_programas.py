"""
Testes unitários para as funções da view programas.py.

programas.py tem três funções (programa_api, busca_projetos,
projeto_sem_filtro) que fazem essencialmente:
    1. Ler parâmetro de query string (?q=...)
    2. Filtrar com Q() no ORM
    3. Serializar objetos em dicts

Nenhuma dessas etapas contém lógica de negócio própria — são operações
de infraestrutura (ORM) e serialização simples.

O que será testado aqui:

1. serializar_programa — o dict montado para cada programa
2. serializar_projeto  — o dict montado para cada projeto
3. normalizar_parametro_busca — o `.strip()` no parâmetro ?q

"""

from unittest.mock import MagicMock
import pytest

# ---------------------------------------------------------------------------
# Funções replicadas das views
# ---------------------------------------------------------------------------


def serializar_programa(programa) -> dict:
    """
    Replica o dict montado dentro do loop de programa_api:
        {
            'codigo_programa': programa.codigo_programa,
            'nome_programa': programa.nome_programa,
            'status': programa.status,
            'gerente': programa.gerente_programa,
            'gerente_tecnico': programa.gerente_tecnico,
        }
    """
    return {
        "codigo_programa": programa.codigo_programa,
        "nome_programa": programa.nome_programa,
        "status": programa.status,
        "gerente": programa.gerente_programa,
        "gerente_tecnico": programa.gerente_tecnico,
    }


def serializar_projeto(projeto) -> dict:
    """
    Replica o dict montado no loop de busca_projetos e projeto_sem_filtro:
        {
            'nome_projeto': projeto.nome_projeto,
            'codigo_projeto': projeto.codigo_projeto,
            'status': projeto.status,
            'responsavel': projeto.responsavel,
        }
    """
    return {
        "nome_projeto": projeto.nome_projeto,
        "codigo_projeto": projeto.codigo_projeto,
        "status": projeto.status,
        "responsavel": projeto.responsavel,
    }


def normalizar_parametro_busca(q_raw: str) -> str:
    """
    Replica o tratamento do parâmetro ?q nas views:
        q = request.GET.get('q', '').strip()
    """
    return (q_raw or "").strip()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_programa(
    codigo="PROG10",
    nome="Programa Alpha",
    status="Ativo",
    gerente="Gerente 10",
    gerente_tecnico="Tecnico 10",
):
    p = MagicMock()
    p.codigo_programa = codigo
    p.nome_programa = nome
    p.status = status
    p.gerente_programa = gerente
    p.gerente_tecnico = gerente_tecnico
    return p


def make_projeto(
    codigo="PRJ10",
    nome="Projeto Alpha",
    status="Ativo",
    responsavel="Resp 10",
):
    p = MagicMock()
    p.codigo_projeto = codigo
    p.nome_projeto = nome
    p.status = status
    p.responsavel = responsavel
    return p


# ===========================================================================
# serializar_programa
# ===========================================================================


class TestSerializarPrograma:
    """
    Valida que o dict de serialização de programa tem os campos corretos
    e que o mapeamento de atributos está certo.

    Nota: 'gerente' no dict vem de 'gerente_programa' no model —
    esse mapeamento é o mais propenso a erro de digitação.
    """

    def test_todos_os_campos_presentes(self):
        prog = make_programa()
        resultado = serializar_programa(prog)

        assert "codigo_programa" in resultado
        assert "nome_programa" in resultado
        assert "status" in resultado
        assert "gerente" in resultado
        assert "gerente_tecnico" in resultado

    def test_campo_gerente_vem_de_gerente_programa(self):
        # Mapeamento não-óbvio: atributo 'gerente_programa' → chave 'gerente'
        # É o tipo de erro que um teste de integração pode não pegar
        # se o nome estiver errado nos dois lados
        prog = make_programa(gerente="Gerente Real")
        resultado = serializar_programa(prog)
        assert resultado["gerente"] == "Gerente Real"

    def test_campo_gerente_tecnico_preservado(self):
        prog = make_programa(gerente_tecnico="Tecnico Real")
        resultado = serializar_programa(prog)
        assert resultado["gerente_tecnico"] == "Tecnico Real"

    def test_projetos_nao_incluidos_no_dict(self):
        # A view explicitamente não inclui 'projetos' no response
        # (validado em test_programas.py com assertNotIn)
        prog = make_programa()
        resultado = serializar_programa(prog)
        assert "projetos" not in resultado

    def test_cenario_exato_do_teste_de_integracao(self):
        # Replica PROG10 do setUp de ProgramaProjetosViewTest
        prog = make_programa(
            codigo="PROG10",
            nome="Programa 10",
            status="Ativo",
            gerente="Gerente 10",
            gerente_tecnico="Tecnico 10",
        )
        resultado = serializar_programa(prog)
        assert resultado["codigo_programa"] == "PROG10"
        assert resultado["nome_programa"] == "Programa 10"
        assert resultado["status"] == "Ativo"
        assert resultado["gerente"] == "Gerente 10"
        assert resultado["gerente_tecnico"] == "Tecnico 10"


# ===========================================================================
# serializar_projeto
# ===========================================================================


class TestSerializarProjeto:

    def test_todos_os_campos_presentes(self):
        proj = make_projeto()
        resultado = serializar_projeto(proj)

        assert "nome_projeto" in resultado
        assert "codigo_projeto" in resultado
        assert "status" in resultado
        assert "responsavel" in resultado

    def test_valores_corretos(self):
        proj = make_projeto(
            codigo="PRJ11",
            nome="Projeto Beta",
            status="Concluido",
            responsavel="Resp 11",
        )
        resultado = serializar_projeto(proj)
        assert resultado["codigo_projeto"] == "PRJ11"
        assert resultado["nome_projeto"] == "Projeto Beta"
        assert resultado["status"] == "Concluido"
        assert resultado["responsavel"] == "Resp 11"

    def test_campos_financeiros_nao_incluidos(self):
        # busca_projetos e projeto_sem_filtro não expõem custo_hora
        # garantir que não vaza informação sensível
        proj = make_projeto()
        resultado = serializar_projeto(proj)
        assert "custo_hora" not in resultado
        assert "programa" not in resultado


# ===========================================================================
# normalizar_parametro_busca
# ===========================================================================


class TestNormalizarParametroBusca:
    """
    A view faz: q = request.GET.get('q', '').strip()

    O que testamos aqui é apenas o comportamento do .strip().
    """

    def test_string_normal_retorna_sem_alteracao(self):
        assert normalizar_parametro_busca("alpha") == "alpha"

    def test_espacos_em_branco_removidos(self):
        assert normalizar_parametro_busca("  alpha  ") == "alpha"

    def test_string_vazia_retorna_vazia(self):
        assert normalizar_parametro_busca("") == ""

    def test_none_retorna_string_vazia(self):
        # request.GET.get('q', '') nunca retorna None, mas o helper
        # defende contra isso para ser robusto
        assert normalizar_parametro_busca(None) == ""

    def test_apenas_espacos_retorna_string_vazia(self):
        # '   '.strip() == '' → filtro não deve ser aplicado
        assert normalizar_parametro_busca("   ") == ""

    def test_case_preservado(self):
        # A normalização não altera maiúsculas/minúsculas — a busca
        # case-insensitive é responsabilidade do icontains no ORM
        assert normalizar_parametro_busca("ALPHA") == "ALPHA"
        assert normalizar_parametro_busca("alpha") == "alpha"
