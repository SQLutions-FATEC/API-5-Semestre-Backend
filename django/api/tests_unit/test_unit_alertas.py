"""
Testes unitários para as funções auxiliares da view alertas.py.

"""

from datetime import date, timedelta
from unittest.mock import MagicMock
import pytest

from api.views.alertas import (
    _adiciona_pedido_atrasado,
    _adiciona_pedido_prioritario_pendente,
    _adiciona_material_pedido_recente,
    _serializa_pedido_recente,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HOJE = date(2024, 6, 15)
ONTEM = HOJE - timedelta(days=1)
AMANHA = HOJE + timedelta(days=1)
HA_31_DIAS = HOJE - timedelta(days=31)
HA_29_DIAS = HOJE - timedelta(days=29)


def make_compra(
    numero_pedido="PED01",
    status="Aberto",
    prioridade="Normal",
    material_id=1,
    valor_total=100.0,
    numero_solicitacao="S01",
):
    """
    Cria um objeto falso de FatoCompra usando MagicMock.
    """
    compra = MagicMock()
    compra.numero_pedido = numero_pedido
    compra.status = status
    compra.valor_total = valor_total
    compra.solicitacao.prioridade = prioridade
    compra.solicitacao.material_id = material_id
    compra.solicitacao.numero_solicitacao = numero_solicitacao
    return compra


# ===========================================================================
# _adiciona_pedido_atrasado
# ===========================================================================


class TestAdicionaPedidoAtrasado:
    """
    Regras validadas:
    1. Só adiciona se status for 'aberto' ou 'pendente' (já normalizado)
    2. Só adiciona se data_previsao_entrega < data_atual
    3. Calcula dias_atraso corretamente
    4. Ignora se data_previsao_entrega for None
    """

    def test_pedido_aberto_atrasado_e_adicionado(self):
        lista = []
        compra = make_compra(status="Aberto")
        _adiciona_pedido_atrasado(lista, compra, HOJE, ONTEM, "aberto")
        assert len(lista) == 1
        assert lista[0]["numero_pedido"] == "PED01"

    def test_pedido_pendente_atrasado_e_adicionado(self):
        lista = []
        compra = make_compra(status="Pendente")
        _adiciona_pedido_atrasado(lista, compra, HOJE, ONTEM, "pendente")
        assert len(lista) == 1

    def test_dias_atraso_calculado_corretamente(self):
        # HOJE - ONTEM = 1 dia de atraso
        lista = []
        compra = make_compra()
        _adiciona_pedido_atrasado(lista, compra, HOJE, ONTEM, "aberto")
        assert lista[0]["dias_atraso"] == 1

    def test_dias_atraso_multiplos_dias(self):
        lista = []
        compra = make_compra()
        ha_10_dias = HOJE - timedelta(days=10)
        _adiciona_pedido_atrasado(lista, compra, HOJE, ha_10_dias, "aberto")
        assert lista[0]["dias_atraso"] == 10

    def test_previsao_hoje_nao_e_atraso(self):
        # data_atual <= data_previsao → não adiciona (limite exato)
        lista = []
        compra = make_compra()
        _adiciona_pedido_atrasado(lista, compra, HOJE, HOJE, "aberto")
        assert lista == []

    def test_previsao_futura_nao_e_atraso(self):
        lista = []
        compra = make_compra()
        _adiciona_pedido_atrasado(lista, compra, HOJE, AMANHA, "aberto")
        assert lista == []

    def test_status_concluido_ignorado_mesmo_atrasado(self):
        lista = []
        compra = make_compra(status="Concluída")
        _adiciona_pedido_atrasado(lista, compra, HOJE, ONTEM, "concluída")
        assert lista == []

    def test_status_enviado_ignorado(self):
        # 'enviado' não está em {'aberto', 'pendente'}
        lista = []
        compra = make_compra(status="Enviado")
        _adiciona_pedido_atrasado(lista, compra, HOJE, ONTEM, "enviado")
        assert lista == []

    def test_data_previsao_none_ignorado(self):
        # Pedido sem data de previsão não deve causar erro nem ser adicionado
        lista = []
        compra = make_compra()
        _adiciona_pedido_atrasado(lista, compra, HOJE, None, "aberto")
        assert lista == []

    def test_data_previsao_isoformat_no_retorno(self):
        lista = []
        compra = make_compra()
        _adiciona_pedido_atrasado(lista, compra, HOJE, ONTEM, "aberto")
        assert lista[0]["data_previsao_entrega"] == ONTEM.isoformat()

    def test_status_original_preservado_no_retorno(self):
        # O status retornado é o original do compra, não o normalizado
        lista = []
        compra = make_compra(status="Aberto")
        _adiciona_pedido_atrasado(lista, compra, HOJE, ONTEM, "aberto")
        assert lista[0]["status"] == "Aberto"

    def test_multiplos_pedidos_atrasados_acumulam_na_lista(self):
        lista = []
        for i in range(3):
            compra = make_compra(numero_pedido=f"PED0{i}")
            _adiciona_pedido_atrasado(lista, compra, HOJE, ONTEM, "aberto")
        assert len(lista) == 3


# ===========================================================================
# _adiciona_pedido_prioritario_pendente
# ===========================================================================


class TestAdicionaPedidoPrioritarioPendente:
    """
    Regras validadas:
    1. Só adiciona prioridade 'alta' ou 'urgente' (já normalizado)
    2. Só adiciona se status for 'aberto' ou 'enviado' (já normalizado)
    3. Formata data_pedido como isoformat (ou None se ausente)
    """

    def test_prioridade_alta_status_aberto_e_adicionado(self):
        lista = []
        compra = make_compra(status="Aberto", prioridade="Alta")
        _adiciona_pedido_prioritario_pendente(lista, compra, HOJE, "alta", "aberto")
        assert len(lista) == 1

    def test_prioridade_urgente_status_enviado_e_adicionado(self):
        lista = []
        compra = make_compra(status="Enviado", prioridade="Urgente")
        _adiciona_pedido_prioritario_pendente(lista, compra, HOJE, "urgente", "enviado")
        assert len(lista) == 1

    def test_prioridade_normal_ignorada(self):
        lista = []
        compra = make_compra(prioridade="Normal")
        _adiciona_pedido_prioritario_pendente(lista, compra, HOJE, "normal", "aberto")
        assert lista == []

    def test_prioridade_alta_status_concluido_ignorado(self):
        # Alta prioridade mas já concluído — não é mais pendente
        lista = []
        compra = make_compra(status="Concluída", prioridade="Alta")
        _adiciona_pedido_prioritario_pendente(lista, compra, HOJE, "alta", "concluída")
        assert lista == []

    def test_prioridade_urgente_status_cancelado_ignorado(self):
        lista = []
        compra = make_compra(status="Cancelado", prioridade="Urgente")
        _adiciona_pedido_prioritario_pendente(
            lista, compra, HOJE, "urgente", "cancelado"
        )
        assert lista == []

    def test_data_pedido_none_retorna_none_no_campo(self):
        lista = []
        compra = make_compra(prioridade="Alta")
        _adiciona_pedido_prioritario_pendente(lista, compra, None, "alta", "aberto")
        assert lista[0]["data_pedido"] is None

    def test_data_pedido_formatada_como_isoformat(self):
        lista = []
        compra = make_compra(prioridade="Alta")
        _adiciona_pedido_prioritario_pendente(lista, compra, HOJE, "alta", "aberto")
        assert lista[0]["data_pedido"] == HOJE.isoformat()

    def test_prioridade_original_preservada_no_retorno(self):
        lista = []
        compra = make_compra(prioridade="Alta")
        _adiciona_pedido_prioritario_pendente(lista, compra, HOJE, "alta", "aberto")
        assert lista[0]["prioridade"] == "Alta"


# ===========================================================================
# _adiciona_material_pedido_recente
# ===========================================================================


class TestAdicionaMaterialPedidoRecente:
    """
    Regras validadas:
    1. Adiciona material_id ao set se data_pedido >= limite_pedido_recente
    2. Ignora se data_pedido < limite (pedido antigo)
    3. Ignora se data_pedido for None
    4. O set acumula IDs de múltiplos pedidos recentes
    """

    def _limite(self):
        return HOJE - timedelta(days=30)

    def test_pedido_recente_adiciona_material_id_ao_set(self):
        ids = set()
        compra = make_compra(material_id=42)
        _adiciona_material_pedido_recente(ids, compra, HA_29_DIAS, self._limite())
        assert 42 in ids

    def test_pedido_no_limite_exato_e_considerado_recente(self):
        # data_pedido == limite → >= limite → deve adicionar
        ids = set()
        compra = make_compra(material_id=42)
        limite = self._limite()
        _adiciona_material_pedido_recente(ids, compra, limite, limite)
        assert 42 in ids

    def test_pedido_anterior_ao_limite_nao_adiciona(self):
        ids = set()
        compra = make_compra(material_id=42)
        _adiciona_material_pedido_recente(ids, compra, HA_31_DIAS, self._limite())
        assert 42 not in ids

    def test_data_pedido_none_nao_adiciona_e_nao_causa_erro(self):
        ids = set()
        compra = make_compra(material_id=42)
        _adiciona_material_pedido_recente(ids, compra, None, self._limite())
        assert len(ids) == 0

    def test_multiplos_materiais_recentes_acumulam_no_set(self):
        ids = set()
        for material_id in [1, 2, 3]:
            compra = make_compra(material_id=material_id)
            _adiciona_material_pedido_recente(ids, compra, HA_29_DIAS, self._limite())
        assert ids == {1, 2, 3}

    def test_mesmo_material_em_pedidos_diferentes_nao_duplica_no_set(self):
        # set garante unicidade — dois pedidos do mesmo material = um ID no set
        ids = set()
        for _ in range(3):
            compra = make_compra(material_id=99)
            _adiciona_material_pedido_recente(ids, compra, HA_29_DIAS, self._limite())
        assert ids == {99}


# ===========================================================================
# _serializa_pedido_recente
# ===========================================================================


class TestSerializaPedidoRecente:
    """
    Regras validadas:
    1. Estrutura do retorno tem a chave 'pedido'
    2. Todos os campos esperados estão presentes
    3. valor_total é convertido para float
    4. Datas são formatadas como isoformat (ou None se ausente)
    """

    def _make_compra_com_datas(self, data_pedido=None, data_previsao=None):
        """
        _serializa_pedido_recente chama _dim_data_para_date internamente,
        então precisamos mockar o retorno dessa conversão via data_pedido
        e data_previsao_entrega como atributos do objeto compra.

        Como _dim_data_para_date é chamada dentro da função, mockamos
        o objeto compra para que _dim_data_para_date receba algo válido
        e retorne as datas que queremos.
        """
        from unittest.mock import patch

        compra = MagicMock()
        compra.numero_pedido = "PED01"
        compra.status = "Enviado"
        compra.valor_total = 250.50
        compra.solicitacao.numero_solicitacao = "S01"

        # Patchamos _dim_data_para_date para retornar nossas datas fixas
        self._patch_data_pedido = data_pedido
        self._patch_data_previsao = data_previsao
        return compra

    def test_retorno_tem_chave_pedido(self):
        from unittest.mock import patch

        compra = MagicMock()
        compra.numero_pedido = "PED01"
        compra.status = "Enviado"
        compra.valor_total = 100.0
        compra.solicitacao.numero_solicitacao = "S01"

        with patch("api.views.alertas._dim_data_para_date", return_value=HOJE):
            resultado = _serializa_pedido_recente(compra)

        assert "pedido" in resultado

    def test_todos_campos_presentes_no_retorno(self):
        from unittest.mock import patch

        compra = MagicMock()
        compra.numero_pedido = "PED01"
        compra.status = "Enviado"
        compra.valor_total = 250.50
        compra.solicitacao.numero_solicitacao = "S01"

        with patch("api.views.alertas._dim_data_para_date", return_value=HOJE):
            resultado = _serializa_pedido_recente(compra)

        pedido = resultado["pedido"]
        assert "numero_pedido" in pedido
        assert "status" in pedido
        assert "valor_total" in pedido
        assert "data_pedido" in pedido
        assert "data_previsao_entrega" in pedido
        assert "solicitacao_numero" in pedido

    def test_valor_total_convertido_para_float(self):
        from unittest.mock import patch
        from decimal import Decimal

        compra = MagicMock()
        compra.numero_pedido = "PED01"
        compra.status = "Enviado"
        compra.valor_total = Decimal("250.50")
        compra.solicitacao.numero_solicitacao = "S01"

        with patch("api.views.alertas._dim_data_para_date", return_value=HOJE):
            resultado = _serializa_pedido_recente(compra)

        assert isinstance(resultado["pedido"]["valor_total"], float)
        assert resultado["pedido"]["valor_total"] == 250.50

    def test_datas_formatadas_como_isoformat(self):
        from unittest.mock import patch

        compra = MagicMock()
        compra.numero_pedido = "PED01"
        compra.status = "Enviado"
        compra.valor_total = 100.0
        compra.solicitacao.numero_solicitacao = "S01"

        with patch("api.views.alertas._dim_data_para_date", return_value=HOJE):
            resultado = _serializa_pedido_recente(compra)

        assert resultado["pedido"]["data_pedido"] == HOJE.isoformat()
        assert resultado["pedido"]["data_previsao_entrega"] == HOJE.isoformat()

    def test_datas_none_retornam_none(self):
        from unittest.mock import patch

        compra = MagicMock()
        compra.numero_pedido = "PED01"
        compra.status = "Enviado"
        compra.valor_total = 100.0
        compra.solicitacao.numero_solicitacao = "S01"

        with patch("api.views.alertas._dim_data_para_date", return_value=None):
            resultado = _serializa_pedido_recente(compra)

        assert resultado["pedido"]["data_pedido"] is None
        assert resultado["pedido"]["data_previsao_entrega"] is None
