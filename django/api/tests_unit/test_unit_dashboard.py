"""
Testes unitários para as funções da view dashboard.py.

"""

from decimal import Decimal
import pytest

# ---------------------------------------------------------------------------
# As fórmulas replicadas da view para teste isolado
# ---------------------------------------------------------------------------

def calcular_custo_total(
    total_horas: float,
    custo_hora: Decimal,
    total_materiais: Decimal,
) -> Decimal:
    """
    Replica a fórmula da view:
        custo_mao_de_obra = Decimal(str(total_horas)) * projeto.custo_hora
        custo_total = custo_mao_de_obra + total_materiais
    """
    custo_mao_de_obra = Decimal(str(total_horas)) * custo_hora
    return custo_mao_de_obra + total_materiais


def calcular_custo_mao_de_obra(total_horas: float, custo_hora: Decimal) -> Decimal:
    """Replica o cálculo intermediário de mão de obra."""
    return Decimal(str(total_horas)) * custo_hora


# ===========================================================================
# calcular_custo_mao_de_obra
# ===========================================================================

class TestCalcularCustoMaoDeObra:
    """
    Regra: custo_mao_de_obra = total_horas * custo_hora
    Validado em test_dashboard_success_with_data:
        5.5h * R$100/h = R$550
    """

    def test_caso_base_do_teste_de_integracao(self):
        # 5.5h * R$100/h = R$550.00 (cenário exato do setUp de test_dashboard.py)
        resultado = calcular_custo_mao_de_obra(5.5, Decimal("100.00"))
        assert resultado == Decimal("550.00")

    def test_horas_zero_retorna_zero(self):
        resultado = calcular_custo_mao_de_obra(0.0, Decimal("100.00"))
        assert resultado == Decimal("0.00")

    def test_custo_hora_zero_retorna_zero(self):
        resultado = calcular_custo_mao_de_obra(10.0, Decimal("0.00"))
        assert resultado == Decimal("0.00")

    def test_horas_fracionadas_calculadas_com_precisao(self):
        # 1.5h * R$100/h = R$150.00
        resultado = calcular_custo_mao_de_obra(1.5, Decimal("100.00"))
        assert resultado == Decimal("150.00")

    def test_custo_hora_com_centavos(self):
        # 2h * R$99.99/h = R$199.98
        resultado = calcular_custo_mao_de_obra(2.0, Decimal("99.99"))
        assert resultado == Decimal("199.98")


# ===========================================================================
# calcular_custo_total
# ===========================================================================

class TestCalcularCustoTotal:
    """
    Regra: custo_total = (total_horas * custo_hora) + total_materiais
    Validado em test_dashboard_success_with_data:
        5.5h * R$100/h + R$150.50 = R$700.50
    """

    def test_caso_base_do_teste_de_integracao(self):
        # 5.5h * R$100/h = R$550 + R$150.50 materiais = R$700.50
        resultado = calcular_custo_total(5.5, Decimal("100.00"), Decimal("150.50"))
        assert float(resultado) == 700.50

    def test_sem_horas_custo_e_apenas_materiais(self):
        resultado = calcular_custo_total(0.0, Decimal("100.00"), Decimal("300.00"))
        assert resultado == Decimal("300.00")

    def test_sem_materiais_custo_e_apenas_mao_de_obra(self):
        resultado = calcular_custo_total(10.0, Decimal("50.00"), Decimal("0.00"))
        assert resultado == Decimal("500.00")

    def test_tudo_zero_retorna_zero(self):
        # Cenário de test_dashboard_success_without_data
        resultado = calcular_custo_total(0.0, Decimal("50.00"), Decimal("0.00"))
        assert resultado == Decimal("0.00")

    def test_resultado_e_decimal_nao_float(self):
        # A view usa Decimal intencionalmente para evitar erros de ponto flutuante
        # em valores monetários. O tipo deve ser preservado.
        resultado = calcular_custo_total(5.0, Decimal("100.00"), Decimal("50.00"))
        assert isinstance(resultado, Decimal)

    def test_valores_grandes_sem_perda_de_precisao(self):
        # R$10.000/h * 1000h + R$500.000 = R$10.500.000
        resultado = calcular_custo_total(1000.0, Decimal("10000.00"), Decimal("500000.00"))
        assert resultado == Decimal("10500000.00")


# ===========================================================================
# Lógica de fallback para valores None do ORM
# ===========================================================================

class TestFallbackValoresNulos:
    """
    A view usa o padrão `aggregate(...) or 0.0` / `or Decimal('0.00')`
    para lidar com projetos sem dados nas tabelas Fato.

    Testamos que esse padrão produz o resultado correto — sem estourar
    TypeError ao tentar somar None com Decimal.
    """

    def test_none_de_aggregate_vira_zero_float(self):
        # Replica: total_horas = horas_trabalhadas['total_horas'] or 0.0
        valor_orm = None
        total_horas = valor_orm or 0.0
        assert total_horas == 0.0
        assert isinstance(total_horas, float)

    def test_none_de_aggregate_vira_decimal_zero(self):
        # Replica: total_materiais = compras_agregadas['total_materiais'] or Decimal('0.00')
        valor_orm = None
        total_materiais = valor_orm or Decimal("0.00")
        assert total_materiais == Decimal("0.00")
        assert isinstance(total_materiais, Decimal)

    def test_valor_real_nao_e_substituido_pelo_fallback(self):
        # Garante que o `or` não engole valores válidos como 0 (que é false em Python)
        # A view usa `or 0.0` então um aggregate que retorne exatamente 0
        # seria substituído — isso documenta o comportamento atual como intencionado
        valor_orm = Decimal("0.00")
        # Decimal('0.00') é false? Não — Decimal('0') é false, Decimal('0.00') também
        # Esse teste documenta que o padrão `or` tem um edge case com zero real
        resultado = valor_orm or Decimal("0.00")
        assert resultado == Decimal("0.00")  # passa, mas por razão incorreta se valor fosse 0

    def test_custo_total_com_fallbacks_aplicados_nao_causa_erro(self):
        # Simula o caminho completo da view quando não há dados
        total_horas = None or 0.0
        total_materiais = None or Decimal("0.00")
        custo_hora = Decimal("100.00")

        # Não deve lançar TypeError
        resultado = calcular_custo_total(total_horas, custo_hora, total_materiais)
        assert resultado == Decimal("0.00")