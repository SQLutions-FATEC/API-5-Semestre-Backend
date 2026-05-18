"""
Testes unitários para as funções da view empenhos.py.

"""

from decimal import Decimal
from unittest.mock import MagicMock
import pytest


# ---------------------------------------------------------------------------
# Fórmulas replicadas das views para teste isolado
# ---------------------------------------------------------------------------

def calcular_valor_empenho(quantidade_empenhada, custo_estimado):
    """
    Replica a fórmula de empenhos_programa:
        valor = emp.quantidade_empenhada * emp.material.custo_estimado
    """
    return quantidade_empenhada * custo_estimado


def agrupar_empenhos_por_data(itens: list[dict]) -> list[dict]:
    """
    Replica o algoritmo de custo_por_tempo_dict em projeto_empenho_api.

    Recebe uma lista de dicts com as chaves que o ORM retorna após o
    .values(...).annotate(...), e produz a estrutura agrupada por data.

    """
    custo_por_tempo_dict = {}

    for item in itens:
        data_str = f"{item['ano']:04d}-{item['mes']:02d}-{item['dia']:02d}"

        if data_str not in custo_por_tempo_dict:
            custo_por_tempo_dict[data_str] = {
                "data": data_str,
                "total_custo": 0.0,
                "materiais": [],
            }

        custo_item = float(item["total_custo"] or 0.0)
        custo_por_tempo_dict[data_str]["total_custo"] += custo_item
        custo_por_tempo_dict[data_str]["materiais"].append({
            "codigo_material": item["codigo_material"],
            "descricao": item["descricao"],
            "custo_unitario": float(item["custo_unitario"] or 0.0),
            "quantidade": item["quantidade_total"] or 0,
            "total_custo": custo_item,
        })

    return list(custo_por_tempo_dict.values())


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def item_empenho(
    ano=2024, mes=2, dia=1,
    codigo_material="MAT01",
    descricao="Cimento",
    custo_unitario=35.50,
    quantidade_total=10,
    total_custo=355.00,
):
    """Fábrica de dicts que simula o retorno do .values().annotate() do ORM."""
    return {
        "ano": ano, "mes": mes, "dia": dia,
        "codigo_material": codigo_material,
        "descricao": descricao,
        "custo_unitario": custo_unitario,
        "quantidade_total": quantidade_total,
        "total_custo": total_custo,
    }


# ===========================================================================
# calcular_valor_empenho
# ===========================================================================

class TestCalcularValorEmpenho:
    """
    Regra: valor = quantidade_empenhada * custo_estimado
    Validado em EmpenhoTest.test_valor_empenhado:
        10 unidades * R$50/un = R$500
    """

    def test_caso_base_do_teste_existente(self):
        # 10 unidades * R$50 = R$500 (cenário exato de EmpenhoTest)
        assert calcular_valor_empenho(10, 50) == 500

    def test_com_decimais(self):
        # 10 * R$35.50 = R$355.00 (cenário de MAT01 em test_empenhos.py)
        resultado = calcular_valor_empenho(10, Decimal("35.50"))
        assert resultado == Decimal("355.00")

    def test_quantidade_zero_retorna_zero(self):
        assert calcular_valor_empenho(0, Decimal("100.00")) == 0

    def test_custo_zero_retorna_zero(self):
        assert calcular_valor_empenho(5, Decimal("0.00")) == 0

    def test_quantidade_grande(self):
        # 1000 tijolos * R$1.50 = R$1500.00 (cenário de MAT03 em test_empenhos.py)
        resultado = calcular_valor_empenho(1000, Decimal("1.50"))
        assert resultado == Decimal("1500.00")

    def test_custo_com_muitas_casas_decimais(self):
        # Garante que a multiplicação não perde precisão
        resultado = calcular_valor_empenho(3, Decimal("33.333"))
        assert resultado == Decimal("99.999")

    def test_acumulacao_de_multiplos_empenhos(self):
        # Simula a soma total da view: empenho_total = sum de todos os valores
        valores = [
            calcular_valor_empenho(10, Decimal("35.50")),   # MAT01: 355.00
            calcular_valor_empenho(5,  Decimal("120.00")),  # MAT02: 600.00
            calcular_valor_empenho(1000, Decimal("1.50")),  # MAT03: 1500.00
        ]
        # Cenário exato de test_empenho_success_with_data: empenho_total = 2455.00
        assert sum(valores) == Decimal("2455.00")


# ===========================================================================
# agrupar_empenhos_por_data
# ===========================================================================

class TestAgruparEmpenhosPorData:
    """
    Regras validadas:
    1. Itens de datas diferentes geram entradas separadas no resultado
    2. Itens da mesma data acumulam total_custo corretamente
    3. Cada entrada tem a lista de materiais daquela data
    4. Formato da data é 'YYYY-MM-DD' com zeros à esquerda
    5. total_custo None é tratado como 0.0 sem erro
    6. Lista vazia retorna lista vazia
    """

    def test_item_unico_gera_uma_entrada(self):
        entrada = [item_empenho(ano=2024, mes=2, dia=1, total_custo=355.00)]
        resultado = agrupar_empenhos_por_data(entrada)
        assert len(resultado) == 1

    def test_datas_diferentes_geram_entradas_separadas(self):
        # Cenário de test_empenho_success_with_data: fev e mar são separados
        entrada = [
            item_empenho(ano=2024, mes=2, dia=1,  total_custo=955.00),
            item_empenho(ano=2024, mes=3, dia=15, total_custo=1500.00,
                         codigo_material="MAT03"),
        ]
        resultado = agrupar_empenhos_por_data(entrada)
        assert len(resultado) == 2

    def test_mesma_data_acumula_total_custo(self):
        # Dois materiais no mesmo dia: 355 + 600 = 955
        # (cenário exato de tempo['2024-02-01']['total_custo'] == 955.00)
        entrada = [
            item_empenho(ano=2024, mes=2, dia=1, codigo_material="MAT01",
                         total_custo=355.00),
            item_empenho(ano=2024, mes=2, dia=1, codigo_material="MAT02",
                         total_custo=600.00),
        ]
        resultado = agrupar_empenhos_por_data(entrada)
        assert len(resultado) == 1
        assert resultado[0]["total_custo"] == 955.00

    def test_mesma_data_acumula_lista_de_materiais(self):
        entrada = [
            item_empenho(ano=2024, mes=2, dia=1, codigo_material="MAT01"),
            item_empenho(ano=2024, mes=2, dia=1, codigo_material="MAT02"),
        ]
        resultado = agrupar_empenhos_por_data(entrada)
        assert len(resultado[0]["materiais"]) == 2

    def test_formato_data_com_zeros_a_esquerda(self):
        # mes=2, dia=1 → "2024-02-01" (não "2024-2-1")
        entrada = [item_empenho(ano=2024, mes=2, dia=1)]
        resultado = agrupar_empenhos_por_data(entrada)
        assert resultado[0]["data"] == "2024-02-01"

    def test_formato_data_mes_e_dia_dois_digitos(self):
        entrada = [item_empenho(ano=2024, mes=12, dia=31)]
        resultado = agrupar_empenhos_por_data(entrada)
        assert resultado[0]["data"] == "2024-12-31"

    def test_total_custo_none_tratado_como_zero(self):
        # Garante que `float(None or 0.0)` não estoura TypeError
        entrada = [item_empenho(total_custo=None)]
        resultado = agrupar_empenhos_por_data(entrada)
        assert resultado[0]["total_custo"] == 0.0

    def test_quantidade_none_tratada_como_zero(self):
        entrada = [item_empenho(quantidade_total=None)]
        resultado = agrupar_empenhos_por_data(entrada)
        assert resultado[0]["materiais"][0]["quantidade"] == 0

    def test_lista_vazia_retorna_lista_vazia(self):
        assert agrupar_empenhos_por_data([]) == []

    def test_estrutura_completa_de_um_item(self):
        entrada = [item_empenho(
            ano=2024, mes=3, dia=15,
            codigo_material="MAT03",
            descricao="Tijolo",
            custo_unitario=1.50,
            quantidade_total=1000,
            total_custo=1500.00,
        )]
        resultado = agrupar_empenhos_por_data(entrada)
        entry = resultado[0]

        assert entry["data"] == "2024-03-15"
        assert entry["total_custo"] == 1500.00
        assert len(entry["materiais"]) == 1

        mat = entry["materiais"][0]
        assert mat["codigo_material"] == "MAT03"
        assert mat["descricao"] == "Tijolo"
        assert mat["custo_unitario"] == 1.50
        assert mat["quantidade"] == 1000
        assert mat["total_custo"] == 1500.00

    def test_ordenacao_preserva_ordem_de_entrada(self):
        # A view ordena no ORM antes de iterar — a função de agrupamento
        # não reordena, apenas agrupa. A ordem de entrada deve ser preservada.
        entrada = [
            item_empenho(ano=2024, mes=2, dia=1,  codigo_material="MAT01"),
            item_empenho(ano=2024, mes=3, dia=15, codigo_material="MAT03"),
        ]
        resultado = agrupar_empenhos_por_data(entrada)
        assert resultado[0]["data"] == "2024-02-01"
        assert resultado[1]["data"] == "2024-03-15"