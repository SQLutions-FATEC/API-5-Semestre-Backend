"""
Testes unitários para as views de compras.py.
"""

import json
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from django.test import RequestFactory

from api.views.compras import compras_projeto_api, evolucao_gastos_api

# ===========================================================================
# Helpers e Mocks
# ===========================================================================

@pytest.fixture
def rf():
    """Fixture do RequestFactory para simular requisições HTTP."""
    return RequestFactory()

def criar_mock_projeto(codigo="PROJ01", ano_inicio=2024, mes_inicio=1):
    """Cria um mock para simular a instância de DimProjeto."""
    projeto = MagicMock()
    projeto.codigo_projeto = codigo
    projeto.data_inicio.ano = ano_inicio
    projeto.data_inicio.mes = mes_inicio
    return projeto

def criar_mock_compra(
    numero="PED01",
    emissao=date(2024, 1, 1),
    previsao=date(2024, 1, 11),
    fornecedor="Fornecedor X",
    material="Material Y",
    status="Pendente",
):
    """Cria um mock para simular a instância de FatoCompra e seus relacionamentos."""
    compra = MagicMock()
    compra.numero_pedido = numero
    compra.data_pedido.ano = emissao.year
    compra.data_pedido.mes = emissao.month
    compra.data_pedido.dia = emissao.day
    compra.data_previsao_entrega.ano = previsao.year
    compra.data_previsao_entrega.mes = previsao.month
    compra.data_previsao_entrega.dia = previsao.day
    compra.fornecedor.razao_social = fornecedor
    compra.solicitacao.material.descricao = material
    compra.status = status
    return compra

def setup_mock_compras(mock_fato_compra, mock_get_object, lista_compras):
    """Configura os mocks do ORM para a view de compras."""
    mock_get_object.return_value = criar_mock_projeto()
    
    mock_qs = MagicMock()
    mock_fato_compra.objects.filter.return_value = mock_qs
    mock_qs.select_related.return_value = lista_compras

def setup_mock_gastos(mock_fato_compra, mock_get_object, dados_gastos, ano_inicio=2024, mes_inicio=1):
    """Configura os mocks do ORM para a view de evolução de gastos."""
    mock_get_object.return_value = criar_mock_projeto(ano_inicio=ano_inicio, mes_inicio=mes_inicio)
    
    mock_qs = MagicMock()
    mock_fato_compra.objects.filter.return_value = mock_qs
    mock_qs.values.return_value = mock_qs
    mock_qs.annotate.return_value = mock_qs
    
    # Converte o dicionário {(ano, mes): valor} para o formato gerado pelo banco (.order_by())
    lista_retorno = [
        {'data_pedido__ano': ano, 'data_pedido__mes': mes, 'total': valor}
        for (ano, mes), valor in dados_gastos.items()
    ]
    mock_qs.order_by.return_value = lista_retorno


# ===========================================================================
# Testes da View: compras_projeto_api
# ===========================================================================

@patch('api.views.compras.FatoCompra')
@patch('api.views.compras.get_object_or_404')
class TestComprasProjetoAPI:

    # --- Lógica de dias previstos ---

    def test_dias_previstos_calculados_corretamente(self, mock_get_object, mock_fato_compra, rf):
        # 1 de jan → 11 de jan = 10 dias
        setup_mock_compras(mock_fato_compra, mock_get_object, [
            criar_mock_compra(emissao=date(2024, 1, 1), previsao=date(2024, 1, 11))
        ])
        
        request = rf.get('/api/fake/')
        response = compras_projeto_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert data["pedidos"][0]["dias_previstos_entrega"] == 10

    def test_pedido_emissao_igual_previsao_tem_zero_dias(self, mock_get_object, mock_fato_compra, rf):
        setup_mock_compras(mock_fato_compra, mock_get_object, [
            criar_mock_compra(emissao=date(2024, 1, 1), previsao=date(2024, 1, 1))
        ])
        
        request = rf.get('/api/fake/')
        response = compras_projeto_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert data["pedidos"][0]["dias_previstos_entrega"] == 0

    def test_datas_formatadas_como_string_iso(self, mock_get_object, mock_fato_compra, rf):
        setup_mock_compras(mock_fato_compra, mock_get_object, [
            criar_mock_compra(emissao=date(2024, 3, 5), previsao=date(2024, 4, 20))
        ])
        
        request = rf.get('/api/fake/')
        response = compras_projeto_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert data["pedidos"][0]["emissao"] == "2024-03-05"
        assert data["pedidos"][0]["previsao"] == "2024-04-20"

    def test_campos_originais_preservados_no_retorno(self, mock_get_object, mock_fato_compra, rf):
        setup_mock_compras(mock_fato_compra, mock_get_object, [
            criar_mock_compra(
                numero="PED99", fornecedor="Forn Teste",
                material="Mat Teste", status="Entregue"
            )
        ])
        
        request = rf.get('/api/fake/')
        response = compras_projeto_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert data["pedidos"][0]["numero"]        == "PED99"
        assert data["pedidos"][0]["fornecedor"]    == "Forn Teste"
        assert data["pedidos"][0]["nome_material"] == "Mat Teste"
        assert data["pedidos"][0]["status"]        == "Entregue"

    # --- Lógica de tempo médio ---

    def test_tempo_medio_com_um_pedido(self, mock_get_object, mock_fato_compra, rf):
        # 10 dias / 1 pedido = 10.0
        setup_mock_compras(mock_fato_compra, mock_get_object, [
            criar_mock_compra(emissao=date(2024, 1, 1), previsao=date(2024, 1, 11))
        ])
        
        request = rf.get('/api/fake/')
        response = compras_projeto_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert data["tempo_medio_entrega_dias"] == 10.0

    def test_tempo_medio_com_dois_pedidos(self, mock_get_object, mock_fato_compra, rf):
        # PED01: 10 dias, PED02: 20 dias → média = 15.0
        setup_mock_compras(mock_fato_compra, mock_get_object, [
            criar_mock_compra("PED01", emissao=date(2024, 1, 1), previsao=date(2024, 1, 11)),
            criar_mock_compra("PED02", emissao=date(2024, 1, 1), previsao=date(2024, 1, 21)),
        ])
        
        request = rf.get('/api/fake/')
        response = compras_projeto_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert data["tempo_medio_entrega_dias"] == 15.0

    def test_tempo_medio_arredondado_a_dois_decimais(self, mock_get_object, mock_fato_compra, rf):
        # 11 dias totais / 3 = 3.6666... → deve arredondar para 3.67
        setup_mock_compras(mock_fato_compra, mock_get_object, [
            criar_mock_compra("P1", emissao=date(2024, 1, 1), previsao=date(2024, 1, 4)), # 3 dias
            criar_mock_compra("P2", emissao=date(2024, 1, 1), previsao=date(2024, 1, 5)), # 4 dias
            criar_mock_compra("P3", emissao=date(2024, 1, 1), previsao=date(2024, 1, 5)), # 4 dias
        ])
        
        request = rf.get('/api/fake/')
        response = compras_projeto_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert data["tempo_medio_entrega_dias"] == 3.67

    def test_lista_vazia_retorna_lista_vazia_e_media_zero(self, mock_get_object, mock_fato_compra, rf):
        setup_mock_compras(mock_fato_compra, mock_get_object, [])
        
        request = rf.get('/api/fake/')
        response = compras_projeto_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert data["pedidos"] == []
        assert data["tempo_medio_entrega_dias"] == 0.0

    def test_ordem_dos_itens_preservada(self, mock_get_object, mock_fato_compra, rf):
        setup_mock_compras(mock_fato_compra, mock_get_object, [
            criar_mock_compra("PED01", emissao=date(2024, 1, 1), previsao=date(2024, 1, 5)),
            criar_mock_compra("PED02", emissao=date(2024, 2, 1), previsao=date(2024, 2, 10)),
        ])
        
        request = rf.get('/api/fake/')
        response = compras_projeto_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert data["pedidos"][0]["numero"] == "PED01"
        assert data["pedidos"][1]["numero"] == "PED02"


# ===========================================================================
# Testes da View: evolucao_gastos_api
# ===========================================================================

@patch('api.views.compras.FatoCompra')
@patch('api.views.compras.get_object_or_404')
class TestEvolucaoGastosAPI:

    def test_mes_sem_dados_preenchido_com_zero(self, mock_get_object, mock_fato_compra, rf):
        # Jan e Mar têm dados, Fev deve aparecer com 0.0
        dados = {(2024, 1): 150.0, (2024, 3): 200.0}
        setup_mock_gastos(mock_fato_compra, mock_get_object, dados, ano_inicio=2024, mes_inicio=1)
        
        request = rf.get('/api/fake/')
        response = evolucao_gastos_api(request, "PROJ01")
        data = json.loads(response.content)

        assert len(data) == 3
        assert data[0] == {"data": "2024-01", "total_gasto": 150.0}
        assert data[1] == {"data": "2024-02", "total_gasto": 0.0}
        assert data[2] == {"data": "2024-03", "total_gasto": 200.0}

    def test_sem_lacunas_quando_todos_os_meses_tem_dados(self, mock_get_object, mock_fato_compra, rf):
        dados = {(2024, 1): 100.0, (2024, 2): 200.0, (2024, 3): 300.0}
        setup_mock_gastos(mock_fato_compra, mock_get_object, dados, ano_inicio=2024, mes_inicio=1)
        
        request = rf.get('/api/fake/')
        response = evolucao_gastos_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert len(data) == 3
        assert [r["total_gasto"] for r in data] == [100.0, 200.0, 300.0]

    def test_virada_de_ano_tratada_corretamente(self, mock_get_object, mock_fato_compra, rf):
        dados = {(2023, 11): 500.0, (2024, 2): 300.0}
        setup_mock_gastos(mock_fato_compra, mock_get_object, dados, ano_inicio=2023, mes_inicio=11)
        
        request = rf.get('/api/fake/')
        response = evolucao_gastos_api(request, "PROJ01")
        data = json.loads(response.content)

        datas = [r["data"] for r in data]
        assert datas == ["2023-11", "2023-12", "2024-01", "2024-02"]
        assert data[1]["total_gasto"] == 0.0  # Dez/2023
        assert data[2]["total_gasto"] == 0.0  # Jan/2024

    def test_compra_antes_do_projeto_recua_o_inicio(self, mock_get_object, mock_fato_compra, rf):
        # Projeto começa em Jan/2024 mas há compra em Dez/2023
        dados = {(2023, 12): 50.0, (2024, 1): 150.0, (2024, 3): 200.0}
        setup_mock_gastos(mock_fato_compra, mock_get_object, dados, ano_inicio=2024, mes_inicio=1)
        
        request = rf.get('/api/fake/')
        response = evolucao_gastos_api(request, "PROJ01")
        data = json.loads(response.content)

        assert len(data) == 4
        assert data[0]["data"] == "2023-12"
        assert data[0]["total_gasto"] == 50.0

    def test_compra_no_mesmo_mes_do_inicio_nao_recua(self, mock_get_object, mock_fato_compra, rf):
        dados = {(2024, 1): 100.0}
        setup_mock_gastos(mock_fato_compra, mock_get_object, dados, ano_inicio=2024, mes_inicio=1)
        
        request = rf.get('/api/fake/')
        response = evolucao_gastos_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert len(data) == 1
        assert data[0]["data"] == "2024-01"

    def test_um_unico_mes_com_dados_retorna_lista_com_um_item(self, mock_get_object, mock_fato_compra, rf):
        dados = {(2024, 6): 999.0}
        setup_mock_gastos(mock_fato_compra, mock_get_object, dados, ano_inicio=2024, mes_inicio=6)
        
        request = rf.get('/api/fake/')
        response = evolucao_gastos_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert len(data) == 1
        assert data[0] == {"data": "2024-06", "total_gasto": 999.0}

    def test_mes_com_um_digito_formatado_com_zero_a_esquerda(self, mock_get_object, mock_fato_compra, rf):
        dados = {(2024, 3): 100.0}
        setup_mock_gastos(mock_fato_compra, mock_get_object, dados, ano_inicio=2024, mes_inicio=3)
        
        request = rf.get('/api/fake/')
        response = evolucao_gastos_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert data[0]["data"] == "2024-03"

    def test_dados_vazios_retorna_lista_vazia(self, mock_get_object, mock_fato_compra, rf):
        setup_mock_gastos(mock_fato_compra, mock_get_object, {}, ano_inicio=2024, mes_inicio=1)
        
        request = rf.get('/api/fake/')
        response = evolucao_gastos_api(request, "PROJ01")
        data = json.loads(response.content)
        
        assert data == []