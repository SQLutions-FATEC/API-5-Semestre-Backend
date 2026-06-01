"""
Testes unitários para as funções utilitárias (utils).

As lógicas testáveis de forma isolada incluem:
1. obter_projeto - Garantir que o atalho do get_object_or_404 atue corretamente.
2. formatar_data_dim - Garantir padronização YYYY-MM-DD e tolerância a falhas.
3. _normaliza_texto - Garantir remoção de acentos, lowercasing e fallback p/ None.
4. _dim_data_para_date - Garantir a conversão segura para um objeto datetime.date.
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from django.http import Http404

# Supondo que as funções originais estejam no arquivo api.views.utils
# Ajuste o import conforme o caminho real no seu projeto.
from api.views.utils import (
    obter_projeto,
    formatar_data_dim,
    _normaliza_texto,
    _dim_data_para_date
)
from api.models import DimProjeto


# ===========================================================================
# obter_projeto
# ===========================================================================

class TestObterProjeto:
    """
    Garante que a função encapsula corretamente a chamada ao get_object_or_404
    para o modelo DimProjeto usando o campo codigo_projeto, repassando a exceção.
    """

    @patch("api.views.utils.get_object_or_404")
    def test_retorna_projeto_existente(self, mock_get_object_or_404):
        # Configura o mock para retornar um projeto simulado
        mock_projeto = MagicMock()
        mock_get_object_or_404.return_value = mock_projeto
        
        resultado = obter_projeto("PRJ-001")
        
        # Verifica se o Django orm shortcut foi chamado com os argumentos exatos
        mock_get_object_or_404.assert_called_once_with(DimProjeto, codigo_projeto="PRJ-001")
        assert resultado == mock_projeto

    @patch("api.views.utils.get_object_or_404")
    def test_levanta_404_quando_nao_encontrado(self, mock_get_object_or_404):
        # Simula o comportamento do Django levantando erro de "não encontrado"
        mock_get_object_or_404.side_effect = Http404()
        
        with pytest.raises(Http404):
            obter_projeto("PRJ-999")


# ===========================================================================
# formatar_data_dim
# ===========================================================================

class TestFormatarDataDim:
    """
    Valida a formatação de um objeto com atributos de data (ano, mes, dia)
    para a string padrão YYYY-MM-DD, lidando adequadamente com Nones e 
    objetos que não possuam os atributos requeridos.
    """

    def test_formata_data_corretamente_com_zeros_a_esquerda(self):
        # Ano 2024, Mês 5 (precisa de zero), Dia 7 (precisa de zero)
        mock_dim = MagicMock(ano=2024, mes=5, dia=7)
        resultado = formatar_data_dim(mock_dim)
        assert resultado == "2024-05-07"

    def test_formata_data_com_meses_e_dias_de_dois_digitos(self):
        mock_dim = MagicMock(ano=2023, mes=11, dia=25)
        resultado = formatar_data_dim(mock_dim)
        assert resultado == "2023-11-25"

    def test_retorna_none_se_entrada_for_none(self):
        assert formatar_data_dim(None) is None

    def test_retorna_none_se_ocorrer_attribute_error(self):
        # Passando um objeto genérico que não possui .ano, .mes, .dia
        mock_invalido = object()
        resultado = formatar_data_dim(mock_invalido)
        assert resultado is None


# ===========================================================================
# _normaliza_texto
# ===========================================================================

class TestNormalizaTexto:
    """
    Garante que o texto é convertido para minúsculas, tem espaços aparados
    nas extremidades e que caracteres acentuados são substituídos.
    """

    def test_remove_acentos_e_converte_para_minusculas(self):
        assert _normaliza_texto("Ação e Reação") == "acao e reacao"
        assert _normaliza_texto("JOÃO MÁRCIO") == "joao marcio"
        assert _normaliza_texto("Pênalti") == "penalti"

    def test_remove_espacos_em_branco_nas_bordas(self):
        assert _normaliza_texto("   Teste Normaliza   ") == "teste normaliza"

    def test_retorna_string_vazia_se_entrada_for_none(self):
        assert _normaliza_texto(None) == ""

    def test_converte_tipos_nao_string_adequadamente(self):
        # A função força str(valor), logo deve conseguir parsear números
        assert _normaliza_texto(12345) == "12345"
        assert _normaliza_texto(10.75) == "10.75"


# ===========================================================================
# _dim_data_para_date
# ===========================================================================

class TestDimDataParaDate:
    """
    Testa a conversão de um objeto de dimensão temporal para um objeto 
    datetime.date nativo do Python, com fallback protetivo contra falhas.
    """

    def test_converte_corretamente_para_objeto_date(self):
        mock_dim = MagicMock(ano=2023, mes=10, dia=15)
        resultado = _dim_data_para_date(mock_dim)
        assert resultado == date(2023, 10, 15)

    def test_retorna_none_se_entrada_for_none(self):
        assert _dim_data_para_date(None) is None

    def test_retorna_none_se_valores_invalidos_para_date_valueerror(self):
        # Ex: Mês 13 ou Dia 32 levantam ValueError internamente no Python
        mock_dim = MagicMock(ano=2023, mes=13, dia=1)
        resultado = _dim_data_para_date(mock_dim)
        assert resultado is None

    def test_retorna_none_se_tipos_invalidos_para_date_typeerror(self):
        # Ex: Passando string em vez de inteiro, o construtor date() levanta TypeError
        mock_dim = MagicMock(ano="2023", mes="Dezembro", dia="quinze")
        resultado = _dim_data_para_date(mock_dim)
        assert resultado is None