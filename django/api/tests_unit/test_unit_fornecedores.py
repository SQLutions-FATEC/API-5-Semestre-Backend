"""
Testes unitários para as views relacionadas a fornecedores.

Cobre as seguintes funcionalidades:
1. fornecedor_api - Detalhes básicos do fornecedor.
2. fornecedor_pedidos_api - Lista de pedidos, status de atraso e filtros de projeto.
3. listagem_fornecedores - Lista geral com filtros complexos e tratamento de duplicados.
"""

import json
from datetime import date
from unittest.mock import MagicMock, patch
import pytest
from django.test import RequestFactory

from api.views.fornecedores import fornecedor_api, fornecedor_pedidos_api
from api.views.fornecedores_list import listagem_fornecedores
from api.models import DimFornecedor, FatoCompra

# ===========================================================================
# Helpers e Mocks Globais
# ===========================================================================


def make_mock_fornecedor(codigo="FORN123", razao_social="Fornecedor Teste", pk=1):
    mock = MagicMock(spec=DimFornecedor)
    mock.pk = pk
    mock.id = pk
    mock.codigo_fornecedor = codigo
    mock.razao_social = razao_social
    mock.cidade = "São Paulo"
    mock.estado = "SP"
    mock.categoria = "Tecnologia"
    mock.status = "Ativo"
    return mock


def make_mock_compra(
    numero="PED-001", status="pendente", data_pedido_val=None, data_prev_val=None
):
    mock = MagicMock(spec=FatoCompra)
    mock.numero_pedido = numero
    mock.status = status
    mock.valor_total = 1500.50
    mock.data_pedido = data_pedido_val
    mock.data_previsao_entrega = data_prev_val

    # Mockando os relacionamentos (solicitacao -> projeto / material)
    mock.solicitacao.projeto.codigo_projeto = "PRJ-001"
    mock.solicitacao.material.descricao = "Material Teste"
    return mock


# ===========================================================================
# Testes: Detalhes do Fornecedor (fornecedor_api)
# ===========================================================================


class TestFornecedorApi:

    @patch("api.views.fornecedores.get_object_or_404")
    def test_retorna_dados_corretos_do_fornecedor(self, mock_get_object):
        # Arrange
        mock_fornecedor = make_mock_fornecedor()
        mock_get_object.return_value = mock_fornecedor
        request = RequestFactory().get('/api/fornecedor/FORN123/')

        # Act
        response = fornecedor_api(request, "FORN123")
        data = json.loads(response.content)

        # Assert
        mock_get_object.assert_called_once_with(
            DimFornecedor, codigo_fornecedor="FORN123"
        )
        assert response.status_code == 200
        assert data["id_fornecedor"] == mock_fornecedor.pk
        assert data["codigo_fornecedor"] == "FORN123"
        assert data["cidade"] == "São Paulo"
        assert data["categoria"] == "Tecnologia"


# ===========================================================================
# Testes: Pedidos do Fornecedor (fornecedor_pedidos_api)
# ===========================================================================


class TestFornecedorPedidosApi:

    @pytest.fixture
    def mock_queryset(self):
        """Prepara um mock da QuerySet encadeável do Django ORM"""
        qs = MagicMock()
        qs.select_related.return_value = qs
        qs.filter.return_value = qs
        qs.order_by.return_value = qs
        return qs

    @patch("api.views.fornecedores.get_object_or_404")
    @patch("api.views.fornecedores.FatoCompra.objects.filter")
    @patch(
        "api.views.fornecedores.date"
    )  # Mockamos a data atual para garantir o atraso
    @patch("api.views.fornecedores._dim_data_para_date")
    def test_calcula_atrasos_corretamente(
        self, mock_dim_date, mock_date, mock_filter, mock_get_object, mock_queryset
    ):
        # Arrange
        mock_get_object.return_value = make_mock_fornecedor()
        mock_filter.return_value = mock_queryset

        # Simula data atual: 10 de Junho
        mock_date.today.return_value = date(2024, 6, 10)

        # Pedido 1: Em atraso (Previsão: 01 de Junho, Status: 'pendente')
        compra_atrasada = make_mock_compra(numero="PED-001", status="Pendente")

        # Pedido 2: No prazo (Previsão: 15 de Junho, Status: 'pendente')
        compra_no_prazo = make_mock_compra(numero="PED-002", status="Pendente")

        # Pedido 3: Entregue (Mesmo que previsão seja 01 de Junho, não deve constar como atrasado)
        compra_entregue = make_mock_compra(numero="PED-003", status="Entregue")

        # Configura o iterador do queryset para retornar a nossa lista de compras
        mock_queryset.__iter__.return_value = [
            compra_atrasada,
            compra_no_prazo,
            compra_entregue,
        ]

        # Controla os retornos sucessivos da conversão de datas simuladas
        mock_dim_date.side_effect = [
            date(2024, 5, 1),
            date(2024, 6, 1),  # Pedido 1 (Pedido, Previsão)
            date(2024, 5, 1),
            date(2024, 6, 15),  # Pedido 2 (Pedido, Previsão)
            date(2024, 5, 1),
            date(2024, 6, 1),  # Pedido 3 (Pedido, Previsão)
        ]

        request = RequestFactory().get('/api/fornecedor/FORN123/pedidos/')

        # Act
        response = fornecedor_pedidos_api(request, "FORN123")
        data = json.loads(response.content)

        # Assert
        assert response.status_code == 200
        assert data["quantidade_pedidos_totais"] == 3
        assert data["quantidade_atrasos"] == 1

        # Validando as flags is_atrasado individuais nos pedidos
        pedidos = data["pedidos"]
        assert pedidos[0]["is_atrasado"] is True  # PED-001
        assert pedidos[1]["is_atrasado"] is False  # PED-002
        assert pedidos[2]["is_atrasado"] is False  # PED-003

    @patch("api.views.fornecedores.get_object_or_404")
    @patch("api.views.fornecedores.FatoCompra.objects.filter")
    def test_aplica_filtro_por_projeto_quando_parametro_presente(
        self, mock_filter, mock_get_object, mock_queryset
    ):
        # Arrange
        mock_get_object.return_value = make_mock_fornecedor()
        mock_filter.return_value = mock_queryset
        mock_queryset.__iter__.return_value = (
            []
        )  # Retorna vazio só para passar pelo loop

        # Passa o parâmetro id_projeto na requisição
        request = RequestFactory().get(
            '/api/fornecedor/FORN123/pedidos/?id_projeto=PRJ-999'
        )

        # Act
        fornecedor_pedidos_api(request, "FORN123")

        # Assert
        # A primeira chamada ao filter é a do fornecedor
        mock_filter.assert_called_once()
        # A chamada secundária do filter (usando Q objects) deve ocorrer
        mock_queryset.filter.assert_called_once()


# ===========================================================================
# Testes: Listagem Geral (listagem_fornecedores)
# ===========================================================================


class TestListagemFornecedores:

    @pytest.fixture
    def mock_qs(self):
        """Mock genérico de QuerySet para suportar os filtros encadeados"""
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.distinct.return_value = qs

        # Simulando um fornecedor retornado pelo mock
        qs.__iter__.return_value = [
            make_mock_fornecedor(codigo="F001", razao_social="Empresa X")
        ]
        return qs

    @patch("api.views.fornecedores_list.DimFornecedor.objects.all")
    def test_retorna_todos_sem_filtros_e_nao_chama_distinct(self, mock_all, mock_qs):
        # Arrange
        mock_all.return_value = mock_qs
        request = RequestFactory().get('/api/fornecedores/')

        # Act
        response = listagem_fornecedores(request)
        data = json.loads(response.content)

        # Assert
        mock_qs.filter.assert_not_called()
        mock_qs.distinct.assert_not_called()
        assert len(data) == 1
        assert data[0]["razao_social"] == "Empresa X"

    @patch("api.views.fornecedores_list.DimFornecedor.objects.all")
    def test_aplica_filtros_simples_sem_chamar_distinct(self, mock_all, mock_qs):
        # Arrange
        mock_all.return_value = mock_qs
        request = RequestFactory().get(
            '/api/fornecedores/?fornecedor_nome=Empresa&fornecedor_cidade=Campinas'
        )

        # Act
        listagem_fornecedores(request)

        # Assert
        # Filter chamado duas vezes (nome e cidade)
        assert mock_qs.filter.call_count == 2
        # Distinct não deve ser chamado para esses campos
        mock_qs.distinct.assert_not_called()

    @patch("api.views.fornecedores_list.DimFornecedor.objects.all")
    def test_aplica_filtro_projeto_e_garante_chamada_distinct(self, mock_all, mock_qs):
        # Arrange
        mock_all.return_value = mock_qs
        request = RequestFactory().get('/api/fornecedores/?projeto_nome=Construcao')

        # Act
        listagem_fornecedores(request)

        # Assert
        # Verifica se tentou filtrar pela string de lookup do ORM correta
        mock_qs.filter.assert_called_with(
            fatocompra__solicitacao__projeto__nome_projeto__icontains='Construcao'
        )
        # Sendo filtro de projeto, deve chamar o distinct()
        mock_qs.distinct.assert_called_once()

    @patch("api.views.fornecedores_list.DimFornecedor.objects.all")
    def test_aplica_filtro_programa_e_garante_chamada_distinct(self, mock_all, mock_qs):
        # Arrange
        mock_all.return_value = mock_qs
        request = RequestFactory().get('/api/fornecedores/?programa_nome=Saude')

        # Act
        listagem_fornecedores(request)

        # Assert
        mock_qs.filter.assert_called_with(
            fatocompra__solicitacao__projeto__programa__nome_programa__icontains='Saude'
        )
        mock_qs.distinct.assert_called_once()
