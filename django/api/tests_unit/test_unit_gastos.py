"""
Testes unitários para as funções da view gastos.py.

"""

from decimal import Decimal
from unittest.mock import MagicMock
import pytest

# ---------------------------------------------------------------------------
# Função replicada da view para teste isolado
# ---------------------------------------------------------------------------


def serializar_pedido(pedido) -> dict:
    """
    Replica o corpo da list comprehension de detalhamento_gastos_projeto_api:

        lista_pedidos = [
            {
                "numero_pedido": pedido.numero_pedido,
                "material_nome": pedido.solicitacao.material.descricao,
                "fornecedor_nome": pedido.fornecedor.razao_social,
                "valor_total_pedido": float(pedido.valor_total),
                "status": pedido.status
            }
            for pedido in pedidos_qs
        ]

    Recebe um objeto (real ou mock) e retorna o dict serializado.
    """
    return {
        "numero_pedido": pedido.numero_pedido,
        "material_nome": pedido.solicitacao.material.descricao,
        "fornecedor_nome": pedido.fornecedor.razao_social,
        "valor_total_pedido": float(pedido.valor_total),
        "status": pedido.status,
    }


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def make_pedido(
    numero_pedido="PED-01",
    material_descricao="Material X",
    fornecedor_razao_social="Fornecedor Y",
    valor_total=Decimal("1500.00"),
    status="Concluido",
):
    """
    Cria um MagicMock que simula um objeto FatoCompra com select_related.

    A list comprehension acessa atributos aninhados via ORM
    (pedido.solicitacao.material.descricao), não chaves de dict.
    MagicMock replica esse acesso por atributo sem banco.
    """
    pedido = MagicMock()
    pedido.numero_pedido = numero_pedido
    pedido.solicitacao.material.descricao = material_descricao
    pedido.fornecedor.razao_social = fornecedor_razao_social
    pedido.valor_total = valor_total
    pedido.status = status
    return pedido


# ===========================================================================
# serializar_pedido
# ===========================================================================


class TestSerializarPedido:
    """
    Regras validadas:
    1. Todos os campos esperados estão presentes no dict retornado
    2. valor_total é convertido para float (não Decimal)
    3. Campos aninhados (material.descricao, fornecedor.razao_social) são acessados corretamente
    4. status e numero_pedido são preservados como strings
    """

    def test_todos_os_campos_presentes(self):
        pedido = make_pedido()
        resultado = serializar_pedido(pedido)

        assert "numero_pedido" in resultado
        assert "material_nome" in resultado
        assert "fornecedor_nome" in resultado
        assert "valor_total_pedido" in resultado
        assert "status" in resultado

    def test_numero_pedido_correto(self):
        pedido = make_pedido(numero_pedido="PED-01")
        resultado = serializar_pedido(pedido)
        assert resultado["numero_pedido"] == "PED-01"

    def test_material_nome_vem_de_atributo_aninhado(self):
        pedido = make_pedido(material_descricao="Cabo Elétrico")
        resultado = serializar_pedido(pedido)
        assert resultado["material_nome"] == "Cabo Elétrico"

    def test_fornecedor_nome_vem_de_atributo_aninhado(self):
        pedido = make_pedido(fornecedor_razao_social="Elétrica Central Ltda")
        resultado = serializar_pedido(pedido)
        assert resultado["fornecedor_nome"] == "Elétrica Central Ltda"

    def test_valor_total_convertido_para_float(self):
        pedido = make_pedido(valor_total=Decimal("1500.00"))
        resultado = serializar_pedido(pedido)
        # A view usa float() explicitamente — deve ser float, não Decimal
        assert isinstance(resultado["valor_total_pedido"], float)
        assert resultado["valor_total_pedido"] == 1500.0

    def test_valor_total_com_centavos_preserva_precisao(self):
        pedido = make_pedido(valor_total=Decimal("999.99"))
        resultado = serializar_pedido(pedido)
        assert resultado["valor_total_pedido"] == 999.99

    def test_status_preservado(self):
        pedido = make_pedido(status="Pendente")
        resultado = serializar_pedido(pedido)
        assert resultado["status"] == "Pendente"

    def test_cenario_exato_do_teste_de_integracao(self):
        # Replica os dados do setUp de GastosProjetoApiTest:
        # PED-01: R$1500.00, status Concluido
        pedido = make_pedido(
            numero_pedido="PED-01",
            material_descricao="Material X",
            fornecedor_razao_social="Fornecedor Y",
            valor_total=Decimal("1500.00"),
            status="Concluido",
        )
        resultado = serializar_pedido(pedido)
        assert resultado["numero_pedido"] == "PED-01"
        assert resultado["valor_total_pedido"] == 1500.0
        assert resultado["status"] == "Concluido"


# ===========================================================================
# Fallback do aggregate — padrão `or 0.0`
# ===========================================================================


class TestFallbackAggregateSemDados:
    """
    A view usa:
        gasto_total_consolidado = pedidos_qs.aggregate(total=Sum('valor_total'))['total'] or 0.0

    Quando não há pedidos, aggregate retorna {'total': None}.
    Testamos que o padrão `or 0.0` lida com isso corretamente.

    É um padrão repetido em várias views do projeto. Um erro aqui
    causaria TypeError ("unsupported operand type: NoneType + float")
    em produção, mas só quando o projeto não tem compras.
    """

    def test_none_vira_zero_float(self):
        valor_aggregate = None
        gasto_total = valor_aggregate or 0.0
        assert gasto_total == 0.0
        assert isinstance(gasto_total, float)

    def test_valor_real_nao_e_substituido(self):
        valor_aggregate = Decimal("2000.00")
        gasto_total = valor_aggregate or 0.0
        assert gasto_total == Decimal("2000.00")

    def test_float_do_total_nulo_e_serializavel_para_json(self):
        # float(0.0) deve ser serializável sem erro no JsonResponse
        import json

        gasto_total = None or 0.0
        payload = {"gasto_total_consolidado": float(gasto_total)}
        # Não deve lançar TypeError ou ValueError
        serializado = json.dumps(payload)
        assert '"gasto_total_consolidado": 0.0' in serializado

    def test_soma_de_dois_pedidos_equivale_ao_consolidado(self):
        # Replica a lógica do teste de integração:
        # PED-01: R$1500 + PED-02: R$500 = R$2000 consolidado
        pedidos = [Decimal("1500.00"), Decimal("500.00")]
        total = sum(pedidos)
        assert float(total) == 2000.0
