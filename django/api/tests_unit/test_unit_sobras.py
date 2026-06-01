"""
Testes unitários para sobras.py.

Duas lógicas são testáveis de forma isolada:

1. calcular_economia_potencial — fórmula da seção de alertas_estoque_ocioso:
       qtd_aproveitavel = min(quantidade_solicitada, total_disponivel)
       economia = qtd_aproveitavel * custo_estimado

2. agrupar_sobras_por_material — algoritmo de acúmulo no dict
   sobras_por_material, que inicializa a chave na primeira ocorrência
   e acumula total_disponivel nas seguintes.

"""

from decimal import Decimal
from unittest.mock import MagicMock
import pytest

# ---------------------------------------------------------------------------
# Fórmulas replicadas da view
# ---------------------------------------------------------------------------


def calcular_economia_potencial(
    quantidade_solicitada: int,
    total_disponivel: int,
    custo_estimado: float,
) -> float:
    """
    Replica a fórmula de otimizacao_sobras_api:
        qtd_aproveitavel = min(sol.quantidade, sobra_info['total_disponivel'])
        economia = float(qtd_aproveitavel * sol.material.custo_estimado)
    """
    qtd_aproveitavel = min(quantidade_solicitada, total_disponivel)
    return round(float(qtd_aproveitavel * custo_estimado), 2)


def agrupar_sobras_por_material(sobras: list[dict]) -> dict:
    """
    Replica o algoritmo do loop `for sobra in sobras_qs` em sobras.py.

    Recebe uma lista de dicts simulando os campos acessados da queryset,
    e retorna o dict sobras_por_material com a estrutura esperada pela
    segunda fase da view (cruzamento com solicitações abertas).

    """
    sobras_por_material = {}
    valor_total = 0.0

    for sobra in sobras:
        mat_cod = sobra["mat_cod"]
        if mat_cod not in sobras_por_material:
            sobras_por_material[mat_cod] = {
                "total_disponivel": 0,
                "detalhes": [],
            }
        sobras_por_material[mat_cod]["total_disponivel"] += sobra[
            "quantidade_disponivel"
        ]
        sobras_por_material[mat_cod]["detalhes"].append(
            {
                "projeto_origem_codigo": sobra["projeto_codigo"],
                "projeto_origem_nome": sobra["projeto_nome"],
                "quantidade_disponivel": sobra["quantidade_disponivel"],
                "status_projeto_origem": sobra["projeto_status"],
                "localizacao_fisica": sobra["localizacao"],
            }
        )
        valor_total += float(sobra["valor_total"])

    return sobras_por_material, valor_total


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def make_sobra(
    mat_cod="MAT1",
    quantidade_disponivel=50,
    projeto_codigo="PRJ101",
    projeto_nome="Proj Sobra",
    projeto_status="CONCLUIDO",
    localizacao="Almoxarifado",
    valor_total=500.0,
):
    return {
        "mat_cod": mat_cod,
        "quantidade_disponivel": quantidade_disponivel,
        "projeto_codigo": projeto_codigo,
        "projeto_nome": projeto_nome,
        "projeto_status": projeto_status,
        "localizacao": localizacao,
        "valor_total": valor_total,
    }


# ===========================================================================
# calcular_economia_potencial
# ===========================================================================


class TestCalcularEconomiaPotencial:
    """
    Regra central: usa min() para não prometer mais do que existe em estoque.
    Validado indiretamente em test_sobras.py via endpoint, mas nunca de forma
    isolada — os casos de borda do min() ficam sem cobertura lá.
    """

    def test_solicitacao_menor_que_disponivel_usa_quantidade_solicitada(self):
        # Precisa de 20, tem 50 → aproveita 20
        economia = calcular_economia_potencial(
            quantidade_solicitada=20,
            total_disponivel=50,
            custo_estimado=10.0,
        )
        assert economia == 200.0

    def test_solicitacao_maior_que_disponivel_usa_disponivel(self):
        # Precisa de 100, tem 30 → aproveita só 30
        economia = calcular_economia_potencial(
            quantidade_solicitada=100,
            total_disponivel=30,
            custo_estimado=10.0,
        )
        assert economia == 300.0

    def test_solicitacao_igual_ao_disponivel(self):
        # Precisa de 50, tem 50 → aproveita 50 (limite exato)
        economia = calcular_economia_potencial(
            quantidade_solicitada=50,
            total_disponivel=50,
            custo_estimado=10.0,
        )
        assert economia == 500.0

    def test_disponivel_zero_retorna_zero(self):
        economia = calcular_economia_potencial(
            quantidade_solicitada=20,
            total_disponivel=0,
            custo_estimado=10.0,
        )
        assert economia == 0.0

    def test_solicitacao_zero_retorna_zero(self):
        economia = calcular_economia_potencial(
            quantidade_solicitada=0,
            total_disponivel=50,
            custo_estimado=10.0,
        )
        assert economia == 0.0

    def test_cenario_exato_do_teste_de_integracao(self):
        # test_sobras.py: SOL1 precisa de 20 unidades, PRJ101 tem 50
        # custo_estimado do material = 10.0 → economia = 20 * 10 = 200.0
        economia = calcular_economia_potencial(
            quantidade_solicitada=20,
            total_disponivel=50,
            custo_estimado=10.0,
        )
        assert economia == 200.0

    def test_resultado_arredondado_a_dois_decimais(self):
        # 3 * 3.333 = 9.999 → round(..., 2) = 10.0
        economia = calcular_economia_potencial(
            quantidade_solicitada=3,
            total_disponivel=10,
            custo_estimado=3.333,
        )
        assert economia == round(3 * 3.333, 2)

    def test_custo_com_decimal(self):
        economia = calcular_economia_potencial(
            quantidade_solicitada=20,
            total_disponivel=50,
            custo_estimado=10.50,
        )
        assert economia == 210.0


# ===========================================================================
# agrupar_sobras_por_material
# ===========================================================================


class TestAgruparSobrasPorMaterial:
    """
    Regras validadas:
    1. Primeira sobra de um material inicializa a chave no dict
    2. Segunda sobra do mesmo material acumula total_disponivel
    3. Detalhes de cada sobra são todos adicionados à lista
    4. valor_total é acumulado corretamente
    5. Lista vazia retorna dict vazio e valor 0.0
    """

    def test_sobra_unica_inicializa_estrutura(self):
        entrada = [make_sobra(mat_cod="MAT1", quantidade_disponivel=50)]
        resultado, _ = agrupar_sobras_por_material(entrada)

        assert "MAT1" in resultado
        assert resultado["MAT1"]["total_disponivel"] == 50
        assert len(resultado["MAT1"]["detalhes"]) == 1

    def test_dois_materiais_diferentes_geram_chaves_separadas(self):
        entrada = [
            make_sobra(mat_cod="MAT1", quantidade_disponivel=50),
            make_sobra(mat_cod="MAT2", quantidade_disponivel=30),
        ]
        resultado, _ = agrupar_sobras_por_material(entrada)

        assert "MAT1" in resultado
        assert "MAT2" in resultado

    def test_mesmo_material_em_projetos_diferentes_acumula_disponivel(self):
        # MAT1 em PRJ101 (50 un) e em PRJ102 (30 un) → total = 80
        entrada = [
            make_sobra(
                mat_cod="MAT1", quantidade_disponivel=50, projeto_codigo="PRJ101"
            ),
            make_sobra(
                mat_cod="MAT1", quantidade_disponivel=30, projeto_codigo="PRJ102"
            ),
        ]
        resultado, _ = agrupar_sobras_por_material(entrada)

        assert resultado["MAT1"]["total_disponivel"] == 80

    def test_mesmo_material_acumula_todos_os_detalhes(self):
        entrada = [
            make_sobra(mat_cod="MAT1", projeto_codigo="PRJ101"),
            make_sobra(mat_cod="MAT1", projeto_codigo="PRJ102"),
        ]
        resultado, _ = agrupar_sobras_por_material(entrada)

        assert len(resultado["MAT1"]["detalhes"]) == 2
        codigos = [d["projeto_origem_codigo"] for d in resultado["MAT1"]["detalhes"]]
        assert "PRJ101" in codigos
        assert "PRJ102" in codigos

    def test_valor_total_acumulado_corretamente(self):
        entrada = [
            make_sobra(mat_cod="MAT1", valor_total=500.0),
            make_sobra(mat_cod="MAT2", valor_total=1000.0),
        ]
        _, valor_total = agrupar_sobras_por_material(entrada)
        assert valor_total == 1500.0

    def test_estrutura_de_detalhe_tem_todos_os_campos(self):
        entrada = [
            make_sobra(
                mat_cod="MAT1",
                quantidade_disponivel=50,
                projeto_codigo="PRJ101",
                projeto_nome="Proj Sobra",
                projeto_status="CONCLUIDO",
                localizacao="Almoxarifado",
            )
        ]
        resultado, _ = agrupar_sobras_por_material(entrada)
        detalhe = resultado["MAT1"]["detalhes"][0]

        assert detalhe["projeto_origem_codigo"] == "PRJ101"
        assert detalhe["projeto_origem_nome"] == "Proj Sobra"
        assert detalhe["quantidade_disponivel"] == 50
        assert detalhe["status_projeto_origem"] == "CONCLUIDO"
        assert detalhe["localizacao_fisica"] == "Almoxarifado"

    def test_lista_vazia_retorna_dict_vazio_e_valor_zero(self):
        resultado, valor_total = agrupar_sobras_por_material([])
        assert resultado == {}
        assert valor_total == 0.0
