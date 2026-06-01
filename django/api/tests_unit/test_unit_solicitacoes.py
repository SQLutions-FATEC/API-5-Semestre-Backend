"""

Testes unitários para:
solicitacoesLista.py
solicitacoesStats.py

Lógicas testáveis isoladamente:

solicitacoesLista.py:
    1. serializar_solicitacao — montagem do dict por solicitação,
       incluindo o fallback de numero_pedido (None se sem pedido)
       e a conversão de valor_total_estimado para float

solicitacoesStats.py:
    2. calcular_dias_desde_criacao — subtração (hoje - data_criacao).days
       com fallback para 0 quando data_criacao é None
    3. filtrar_prioridades_criticas — a lógica do filter com múltiplos
       valores de prioridade (case-sensitive no ORM, mas testável a nível
       de contrato esperado)

"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
import pytest

# ---------------------------------------------------------------------------
# Fórmulas replicadas de solicitacoesLista.py
# ---------------------------------------------------------------------------


def serializar_solicitacao(sol, data_sol, pedido_vinculado) -> dict:
    """
    Replica o bloco de montagem de dict dentro do loop de listagem_solicitacoes:

        numero_pedido = pedido_vinculado.numero_pedido if pedido_vinculado else None
        lista_detalhes.append({
            "numero_solicitacao": sol.numero_solicitacao,
            "numero_pedido": numero_pedido,
            "nome_material": sol.material.descricao,
            "data_solicitacao": data_sol.isoformat() if data_sol else None,
            "valor_total_estimado": float(sol.valor_total_estimado) if sol.valor_total_estimado else 0.0,
            "status": sol.status
        })

    """
    numero_pedido = pedido_vinculado.numero_pedido if pedido_vinculado else None

    return {
        "numero_solicitacao": sol.numero_solicitacao,
        "numero_pedido": numero_pedido,
        "nome_material": sol.material.descricao,
        "data_solicitacao": data_sol.isoformat() if data_sol else None,
        "valor_total_estimado": (
            float(sol.valor_total_estimado) if sol.valor_total_estimado else 0.0
        ),
        "status": sol.status,
    }


# ---------------------------------------------------------------------------
# Fórmulas replicadas de solicitacoesStats.py
# ---------------------------------------------------------------------------


def calcular_dias_desde_criacao(hoje: date, data_criacao) -> int:
    """
    Replica o cálculo de request_analytics_api:
        dias_pendentes = (hoje - data_criacao).days if data_criacao else 0
    """
    return (hoje - data_criacao).days if data_criacao else 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HOJE = date(2024, 6, 15)


def make_solicitacao(
    numero="S10",
    material_descricao="Placa Mãe",
    valor_total_estimado=Decimal("300.00"),
    status="Aprovada",
):
    sol = MagicMock()
    sol.numero_solicitacao = numero
    sol.material.descricao = material_descricao
    sol.valor_total_estimado = valor_total_estimado
    sol.status = status
    return sol


def make_pedido(numero="PED10"):
    pedido = MagicMock()
    pedido.numero_pedido = numero
    return pedido


# ===========================================================================
# serializar_solicitacao  (solicitacoesLista.py)
# ===========================================================================


class TestSerializarSolicitacao:
    """
    Regras validadas:
    1. Todos os campos esperados estão presentes
    2. numero_pedido é None quando não há pedido vinculado
    3. numero_pedido é preenchido quando há pedido
    4. data_solicitacao é isoformat ou None
    5. valor_total_estimado é convertido para float
    6. valor_total_estimado None retorna 0.0 (sem TypeError)
    """

    def test_todos_os_campos_presentes(self):
        sol = make_solicitacao()
        resultado = serializar_solicitacao(sol, HOJE, make_pedido())

        assert "numero_solicitacao" in resultado
        assert "numero_pedido" in resultado
        assert "nome_material" in resultado
        assert "data_solicitacao" in resultado
        assert "valor_total_estimado" in resultado
        assert "status" in resultado

    def test_sem_pedido_numero_pedido_e_none(self):
        # Cenário de S11 em test_solicitacoes_lista.py: solicitação sem pedido
        sol = make_solicitacao(numero="S11")
        resultado = serializar_solicitacao(sol, HOJE, pedido_vinculado=None)
        assert resultado["numero_pedido"] is None

    def test_com_pedido_numero_pedido_preenchido(self):
        # Cenário de S10 em test_solicitacoes_lista.py: solicitação com PED10
        sol = make_solicitacao(numero="S10")
        pedido = make_pedido(numero="PED10")
        resultado = serializar_solicitacao(sol, HOJE, pedido_vinculado=pedido)
        assert resultado["numero_pedido"] == "PED10"

    def test_data_solicitacao_formatada_como_isoformat(self):
        sol = make_solicitacao()
        resultado = serializar_solicitacao(sol, date(2024, 5, 10), make_pedido())
        assert resultado["data_solicitacao"] == "2024-05-10"

    def test_data_solicitacao_none_retorna_none(self):
        sol = make_solicitacao()
        resultado = serializar_solicitacao(sol, None, make_pedido())
        assert resultado["data_solicitacao"] is None

    def test_valor_total_estimado_convertido_para_float(self):
        sol = make_solicitacao(valor_total_estimado=Decimal("300.00"))
        resultado = serializar_solicitacao(sol, HOJE, make_pedido())
        assert isinstance(resultado["valor_total_estimado"], float)
        assert resultado["valor_total_estimado"] == 300.0

    def test_valor_total_estimado_none_retorna_zero(self):
        # Garante que `float(None)` não estoura — a view usa `if sol.valor_total_estimado`
        sol = make_solicitacao(valor_total_estimado=None)
        resultado = serializar_solicitacao(sol, HOJE, make_pedido())
        assert resultado["valor_total_estimado"] == 0.0

    def test_cenario_exato_s11_sem_pedido_valor_estimado(self):
        # S11: 5 unidades * R$150.00 = R$750.00, sem pedido vinculado
        sol = make_solicitacao(
            numero="S11",
            material_descricao="Placa Mãe",
            valor_total_estimado=Decimal("750.00"),
            status="Pendente",
        )
        resultado = serializar_solicitacao(
            sol, date(2024, 5, 10), pedido_vinculado=None
        )
        assert resultado["numero_pedido"] is None
        assert resultado["valor_total_estimado"] == 750.0
        assert resultado["nome_material"] == "Placa Mãe"

    def test_status_preservado(self):
        sol = make_solicitacao(status="Pendente")
        resultado = serializar_solicitacao(sol, HOJE, None)
        assert resultado["status"] == "Pendente"


# ===========================================================================
# calcular_dias_desde_criacao  (solicitacoesStats.py)
# ===========================================================================


class TestCalcularDiasDesideCriacao:
    """
    Regras validadas:
    1. Diferença em dias calculada corretamente
    2. data_criacao None retorna 0 (sem TypeError)
    3. data_criacao == hoje retorna 0
    4. Cenários exatos de test_solicitacoes.py (5 dias e 2 dias)
    """

    def test_cenario_5_dias_do_teste_de_integracao(self):
        # S02 criada há 5 dias: dias_desde_criacao == 5
        data_criacao = HOJE - timedelta(days=5)
        assert calcular_dias_desde_criacao(HOJE, data_criacao) == 5

    def test_cenario_2_dias_do_teste_de_integracao(self):
        # S03 criada há 2 dias: dias_desde_criacao == 2
        data_criacao = HOJE - timedelta(days=2)
        assert calcular_dias_desde_criacao(HOJE, data_criacao) == 2

    def test_criada_hoje_retorna_zero(self):
        assert calcular_dias_desde_criacao(HOJE, HOJE) == 0

    def test_data_none_retorna_zero_sem_erro(self):
        # Garante que `(hoje - None).days` não estoura TypeError
        assert calcular_dias_desde_criacao(HOJE, None) == 0

    def test_criada_ontem_retorna_um(self):
        ontem = HOJE - timedelta(days=1)
        assert calcular_dias_desde_criacao(HOJE, ontem) == 1

    def test_criada_ha_30_dias(self):
        ha_30_dias = HOJE - timedelta(days=30)
        assert calcular_dias_desde_criacao(HOJE, ha_30_dias) == 30

    def test_resultado_e_inteiro(self):
        data_criacao = HOJE - timedelta(days=5)
        resultado = calcular_dias_desde_criacao(HOJE, data_criacao)
        assert isinstance(resultado, int)
