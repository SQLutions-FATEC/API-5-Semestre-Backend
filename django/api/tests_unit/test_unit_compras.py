"""
Testes unitários para as funções da view compras.py.

"""

from datetime import date
import pytest

from api.views.compras import (
    calcular_dias_e_tempo_medio,
    preencher_serie_temporal,
)


# ===========================================================================
# Helpers
# ===========================================================================

def compra(
    numero="PED01",
    emissao=date(2024, 1, 1),
    previsao=date(2024, 1, 11),
    fornecedor="Fornecedor X",
    material="Material Y",
    status="Pendente",
):
    """Fábrica de dicts de compra com valores padrão sensatos."""
    return {
        "numero_pedido": numero,
        "data_emissao":  emissao,
        "data_previsao": previsao,
        "fornecedor":    fornecedor,
        "nome_material": material,
        "status":        status,
    }


# ===========================================================================
# calcular_dias_e_tempo_medio
# ===========================================================================

class TestCalcularDiasETempMedio:

# ===========================================================================
# Lógica de dias previstos
# ===========================================================================

    def test_dias_previstos_calculados_corretamente(self):
        # 1 de jan → 11 de jan = 10 dias (igual ao PED01 do test_compras.py)
        entrada = [compra(emissao=date(2024, 1, 1), previsao=date(2024, 1, 11))]
        lista, _ = calcular_dias_e_tempo_medio(entrada)
        assert lista[0]["dias_previstos_entrega"] == 10

    def test_pedido_emissao_igual_previsao_tem_zero_dias(self):
        entrada = [compra(emissao=date(2024, 1, 1), previsao=date(2024, 1, 1))]
        lista, _ = calcular_dias_e_tempo_medio(entrada)
        assert lista[0]["dias_previstos_entrega"] == 0

    def test_datas_formatadas_como_string_iso(self):
        entrada = [compra(emissao=date(2024, 3, 5), previsao=date(2024, 4, 20))]
        lista, _ = calcular_dias_e_tempo_medio(entrada)
        assert lista[0]["emissao"] == "2024-03-05"
        assert lista[0]["previsao"] == "2024-04-20"

    def test_campos_originais_preservados_no_retorno(self):
        entrada = [compra(
            numero="PED99",
            fornecedor="Forn Teste",
            material="Mat Teste",
            status="Entregue",
        )]
        lista, _ = calcular_dias_e_tempo_medio(entrada)
        assert lista[0]["numero"]        == "PED99"
        assert lista[0]["fornecedor"]    == "Forn Teste"
        assert lista[0]["nome_material"] == "Mat Teste"
        assert lista[0]["status"]        == "Entregue"

# ===========================================================================
# Lógica de tempo médio
# ===========================================================================

    def test_tempo_medio_com_um_pedido(self):
        # 10 dias / 1 pedido = 10.0
        entrada = [compra(emissao=date(2024, 1, 1), previsao=date(2024, 1, 11))]
        _, tempo_medio = calcular_dias_e_tempo_medio(entrada)
        assert tempo_medio == 10.0

    def test_tempo_medio_com_dois_pedidos(self):
        # PED01: 10 dias, PED02: 20 dias → média = 15.0
        # (exatamente o cenário de test_compras_success_with_data)
        entrada = [
            compra("PED01", emissao=date(2024, 1, 1), previsao=date(2024, 1, 11)),
            compra("PED02", emissao=date(2024, 1, 1), previsao=date(2024, 1, 21)),
        ]
        _, tempo_medio = calcular_dias_e_tempo_medio(entrada)
        assert tempo_medio == 15.0

    def test_tempo_medio_arredondado_a_dois_decimais(self):
        # 10 + 11 + 12 = 33 dias / 3 pedidos = 11.0 (sem casas problemáticas)
        # Para testar arredondamento: 1 + 2 = 3 / 2 = 1.5 (limpo)
        # Caso com divisão não exata: 10 dias / 3 pedidos
        entrada = [
            compra("P1", emissao=date(2024, 1, 1), previsao=date(2024, 1, 4)),   # 3 dias
            compra("P2", emissao=date(2024, 1, 1), previsao=date(2024, 1, 5)),   # 4 dias
            compra("P3", emissao=date(2024, 1, 1), previsao=date(2024, 1, 5)),   # 4 dias
        ]
        # 11 / 3 = 3.6666... → deve arredondar para 3.67
        _, tempo_medio = calcular_dias_e_tempo_medio(entrada)
        assert tempo_medio == 3.67

    def test_lista_vazia_retorna_lista_vazia_e_media_zero(self):
        lista, tempo_medio = calcular_dias_e_tempo_medio([])
        assert lista == []
        assert tempo_medio == 0.0

    def test_ordem_dos_itens_preservada(self):
        entrada = [
            compra("PED01", emissao=date(2024, 1, 1), previsao=date(2024, 1, 5)),
            compra("PED02", emissao=date(2024, 2, 1), previsao=date(2024, 2, 10)),
        ]
        lista, _ = calcular_dias_e_tempo_medio(entrada)
        assert lista[0]["numero"] == "PED01"
        assert lista[1]["numero"] == "PED02"


# ===========================================================================
# preencher_serie_temporal
# ===========================================================================

class TestPreencherSerieTemporal:

    def test_mes_sem_dados_preenchido_com_zero(self):
        # Jan e Mar têm dados, Fev deve aparecer com 0.0
        # (cenário exato de test_evolucao_gastos_success_with_data)
        dados = {
            (2024, 1): 150.0,
            (2024, 3): 200.0,
        }
        resultado = preencher_serie_temporal(dados, ano_inicio=2024, mes_inicio=1)

        assert len(resultado) == 3
        assert resultado[0] == {"data": "2024-01", "total_gasto": 150.0}
        assert resultado[1] == {"data": "2024-02", "total_gasto": 0.0}
        assert resultado[2] == {"data": "2024-03", "total_gasto": 200.0}

    def test_sem_lacunas_quando_todos_os_meses_tem_dados(self):
        dados = {
            (2024, 1): 100.0,
            (2024, 2): 200.0,
            (2024, 3): 300.0,
        }
        resultado = preencher_serie_temporal(dados, ano_inicio=2024, mes_inicio=1)
        assert len(resultado) == 3
        assert [r["total_gasto"] for r in resultado] == [100.0, 200.0, 300.0]

# ===========================================================================
# Lógica de virada de ano
# ===========================================================================
    def test_virada_de_ano_tratada_corretamente(self):
        dados = {
            (2023, 11): 500.0,
            (2024,  2): 300.0,
        }
        resultado = preencher_serie_temporal(dados, ano_inicio=2023, mes_inicio=11)

        datas = [r["data"] for r in resultado]
        assert datas == ["2023-11", "2023-12", "2024-01", "2024-02"]
        assert resultado[1]["total_gasto"] == 0.0  # Dez/2023
        assert resultado[2]["total_gasto"] == 0.0  # Jan/2024

# ===========================================================================
# Lógica de compra anterior ao projeto
# ===========================================================================

    def test_compra_antes_do_projeto_recua_o_inicio(self):
        # Cenário de test_evolucao_gastos_min_date_before_project:
        # Projeto começa em Jan/2024 mas há compra em Dez/2023
        dados = {
            (2023, 12): 50.0,
            (2024,  1): 150.0,
            (2024,  3): 200.0,
        }
        resultado = preencher_serie_temporal(dados, ano_inicio=2024, mes_inicio=1)

        assert len(resultado) == 4
        assert resultado[0]["data"] == "2023-12"
        assert resultado[0]["total_gasto"] == 50.0

    def test_compra_no_mesmo_mes_do_inicio_nao_recua(self):
        dados = {(2024, 1): 100.0}
        resultado = preencher_serie_temporal(dados, ano_inicio=2024, mes_inicio=1)
        assert len(resultado) == 1
        assert resultado[0]["data"] == "2024-01"

    # --- mês único ---

    def test_um_unico_mes_com_dados_retorna_lista_com_um_item(self):
        dados = {(2024, 6): 999.0}
        resultado = preencher_serie_temporal(dados, ano_inicio=2024, mes_inicio=6)
        assert len(resultado) == 1
        assert resultado[0] == {"data": "2024-06", "total_gasto": 999.0}

    # --- formato da saída ---

    def test_mes_com_um_digito_formatado_com_zero_a_esquerda(self):
        dados = {(2024, 3): 100.0}
        resultado = preencher_serie_temporal(dados, ano_inicio=2024, mes_inicio=3)
        assert resultado[0]["data"] == "2024-03"

    def test_dados_vazios_retorna_lista_vazia(self):
        resultado = preencher_serie_temporal({}, ano_inicio=2024, mes_inicio=1)
        assert resultado == []