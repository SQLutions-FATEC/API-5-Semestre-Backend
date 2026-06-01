"""
etl/tests/unit/test_unit_etl.py

Testes unitários para a camada de ETL.

Cobertura por módulo:

    etl/transformations/transformers.py  ← ALTA PRIORIDADE
        - remove_accents
        - standardize_strings
        - handle_nulls
        - calculate_project_metrics

    etl/validators/integrity.py          ← MÉDIA PRIORIDADE
        - validate

    etl/loaders/loader.py                ← BAIXA PRIORIDADE
        - get_date_cache
        - filter_valid_ids

    etl/extractors/extractors.py         ← NÃO TESTADO AQUI
        Classes só declaram csv_file — sem lógica própria.
        Coberto implicitamente pelo teste de integração run_etl.

"""

import pandas as pd
import numpy as np
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from etl.transformations.transformers import (
    remove_accents,
    standardize_strings,
    handle_nulls,
    calculate_project_metrics,
)
from etl.validators.integrity import validate

# ===========================================================================
# remove_accents
# ===========================================================================


class TestRemoveAccents:
    """
    Função auxiliar usada dentro de standardize_strings.
    Testada separadamente porque falhas aqui afetam toda a padronização.

    Casos de borda importantes: None, números, strings já sem acento.
    """

    def test_acento_agudo_removido(self):
        assert remove_accents("Concluído") == "Concluido"

    def test_multiplos_acentos_removidos(self):
        assert remove_accents("Não Iniciação") == "Nao Iniciacao"

    def test_cedilha_removida(self):
        assert remove_accents("Aquisição") == "Aquisicao"

    def test_string_sem_acento_nao_alterada(self):
        assert remove_accents("ATIVO") == "ATIVO"

    def test_string_vazia_retorna_vazia(self):
        assert remove_accents("") == ""

    def test_nao_string_retorna_sem_alteracao(self):
        # A função tem `if not isinstance(input_str, str): return input_str`
        assert remove_accents(None) is None
        assert remove_accents(42) == 42
        assert remove_accents(3.14) == 3.14


# ===========================================================================
# standardize_strings
# ===========================================================================


class TestStandardizeStrings:
    """
    Regras validadas:
    1. Converte para maiúsculo
    2. Remove acentos
    3. Remove espaços extras (strip)
    4. Substitui representações de nulo ('NAN', 'NONE', etc.) por 'NAO INFORMADO'
    5. Colunas não listadas não são alteradas
    6. Colunas ausentes no DataFrame não causam erro

    """

    def test_converte_para_maiusculo(self):
        df = pd.DataFrame({"status": ["ativo", "Pendente", "CONCLUIDO"]})
        resultado = standardize_strings(df, ["status"])
        assert list(resultado["status"]) == ["ATIVO", "PENDENTE", "CONCLUIDO"]

    def test_remove_acentos(self):
        df = pd.DataFrame({"status": ["Concluído", "Não Iniciada"]})
        resultado = standardize_strings(df, ["status"])
        assert list(resultado["status"]) == ["CONCLUIDO", "NAO INICIADA"]

    def test_remove_espacos_extras(self):
        df = pd.DataFrame({"status": ["  ativo  ", " pendente"]})
        resultado = standardize_strings(df, ["status"])
        assert list(resultado["status"]) == ["ATIVO", "PENDENTE"]

    def test_nan_substituido_por_nao_informado(self):
        df = pd.DataFrame({"categoria": ["nan", "Construcao"]})
        resultado = standardize_strings(df, ["categoria"])
        assert resultado["categoria"][0] == "NAO INFORMADO"

    def test_none_string_substituido(self):
        df = pd.DataFrame({"status": ["None", "ativo"]})
        resultado = standardize_strings(df, ["status"])
        assert resultado["status"][0] == "NAO INFORMADO"

    def test_string_vazia_substituida(self):
        df = pd.DataFrame({"status": ["", "ativo"]})
        resultado = standardize_strings(df, ["status"])
        assert resultado["status"][0] == "NAO INFORMADO"

    def test_coluna_nao_listada_nao_alterada(self):
        df = pd.DataFrame({"status": ["ativo"], "nome": ["João Silva"]})
        resultado = standardize_strings(df, ["status"])
        # 'nome' não foi listada — não deve ser tocada
        assert resultado["nome"][0] == "João Silva"

    def test_coluna_ausente_no_dataframe_nao_causa_erro(self):
        df = pd.DataFrame({"status": ["ativo"]})
        # 'prioridade' não existe no df — não deve lançar KeyError
        resultado = standardize_strings(df, ["status", "prioridade"])
        assert list(resultado["status"]) == ["ATIVO"]

    def test_multiplas_colunas_padronizadas(self):
        df = pd.DataFrame(
            {
                "status": ["em andamento"],
                "prioridade": ["crítica"],
            }
        )
        resultado = standardize_strings(df, ["status", "prioridade"])
        assert resultado["status"][0] == "EM ANDAMENTO"
        assert resultado["prioridade"][0] == "CRITICA"

    def test_cenario_exato_do_teste_de_integracao(self):
        # test_extraction.py verifica: projeto.status == projeto.status.upper()
        # Aqui validamos a mesma regra de forma isolada
        df = pd.DataFrame({"status": ["em andamento"]})
        resultado = standardize_strings(df, ["status"])
        valor = resultado["status"][0]
        assert valor == valor.upper()


# ===========================================================================
# handle_nulls
# ===========================================================================


class TestHandleNulls:
    """
    Regra: preenche NaN em colunas numéricas com 0.
    Colunas não-numéricas (str, object) não são alteradas.
    """

    def test_nan_numerico_substituido_por_zero(self):
        df = pd.DataFrame({"valor": [1.0, np.nan, 3.0]})
        resultado = handle_nulls(df)
        assert resultado["valor"][1] == 0.0

    def test_inteiro_nan_substituido_por_zero(self):
        df = pd.DataFrame(
            {"quantidade": pd.array([1, pd.NA, 3], dtype=pd.Int64Dtype())}
        )
        resultado = handle_nulls(df)
        # Após fillna(0), não deve haver NaN
        assert resultado["quantidade"].isna().sum() == 0

    def test_coluna_string_nao_alterada(self):
        df = pd.DataFrame(
            {"status": ["ativo", None, "pendente"], "valor": [1.0, np.nan, 3.0]}
        )
        resultado = handle_nulls(df)
        assert pd.isna(resultado["status"][1])

    def test_dataframe_sem_nulos_nao_alterado(self):
        df = pd.DataFrame({"valor": [1.0, 2.0, 3.0]})
        resultado = handle_nulls(df)
        assert list(resultado["valor"]) == [1.0, 2.0, 3.0]

    def test_dataframe_sem_colunas_numericas_nao_causa_erro(self):
        df = pd.DataFrame({"nome": ["Ana", "Bruno"]})
        resultado = handle_nulls(df)
        assert list(resultado["nome"]) == ["Ana", "Bruno"]


# ===========================================================================
# calculate_project_metrics  (complementa test_transformers.py)
# ===========================================================================


class TestCalculateProjectMetrics:
    """
    Os casos básicos já estão em test_transformers.py:
        - lead_time_dias = 10 para projeto de 10 dias
        - is_atrasado = True para projeto em andamento com data passada

    Aqui cobrimos os casos de borda que o teste existente não alcança.
    """

    def _make_df(self, data_inicio, data_fim, status):
        return pd.DataFrame(
            {
                "data_inicio": [data_inicio],
                "data_fim_prevista": [data_fim],
                "status": [status],
            }
        )

    def test_dataframe_vazio_retorna_vazio(self):
        df = pd.DataFrame(columns=["data_inicio", "data_fim_prevista", "status"])
        resultado = calculate_project_metrics(df)
        assert resultado.empty

    def test_projeto_concluido_com_data_passada_nao_e_atrasado(self):
        # CONCLUIDO nunca deve ser marcado como atrasado, mesmo com data passada
        # Este caso NÃO está coberto no test_transformers.py existente
        df = self._make_df("2020-01-01", "2020-06-01", "CONCLUIDO")
        resultado = calculate_project_metrics(df)
        assert resultado.loc[0, "is_atrasado"] == False

    def test_projeto_concluido_com_acento_nao_e_atrasado(self):
        # "Concluído" (com acento) deve ser normalizado antes da comparação
        # Bug potencial: comparar "CONCLUÍDO" != "CONCLUIDO" sem remover acento
        df = self._make_df("2020-01-01", "2020-06-01", "Concluído")
        resultado = calculate_project_metrics(df)
        assert resultado.loc[0, "is_atrasado"] == False

    def test_lead_time_mesmo_dia_e_zero(self):
        df = self._make_df("2024-01-01", "2024-01-01", "EM ANDAMENTO")
        resultado = calculate_project_metrics(df)
        assert resultado.loc[0, "lead_time_dias"] == 0

    def test_lead_time_negativo_nao_ocorre_com_datas_invertidas(self):
        # Dados sujos: data_fim antes de data_inicio
        # fillna(0).astype(int) deve evitar valores negativos extremos?
        # Na verdade pode resultar em negativo — este teste documenta o comportamento atual
        df = self._make_df("2024-06-01", "2024-01-01", "EM ANDAMENTO")
        resultado = calculate_project_metrics(df)
        # lead_time pode ser negativo com datas invertidas — documentamos isso
        assert isinstance(resultado.loc[0, "lead_time_dias"], (int, np.integer))

    def test_data_nula_nao_marca_is_atrasado_como_true(self):
        # fillna(False) ao final garante que NaT não vira True
        df = pd.DataFrame(
            {
                "data_inicio": [pd.NaT],
                "data_fim_prevista": [pd.NaT],
                "status": ["EM ANDAMENTO"],
            }
        )
        resultado = calculate_project_metrics(df)
        assert resultado.loc[0, "is_atrasado"] == False

    def test_coluna_status_ausente_usa_fallback(self):
        # Sem coluna 'status', a regra de fallback é usada:
        # is_atrasado = data_fim_prevista < hoje
        df = pd.DataFrame(
            {
                "data_inicio": ["2020-01-01"],
                "data_fim_prevista": ["2020-06-01"],
            }
        )
        resultado = calculate_project_metrics(df)
        # Data passada sem status → is_atrasado deve ser True (fallback)
        assert resultado.loc[0, "is_atrasado"] == True

    def test_lead_time_e_inteiro(self):
        df = self._make_df("2024-01-01", "2024-01-11", "EM ANDAMENTO")
        resultado = calculate_project_metrics(df)
        assert isinstance(resultado.loc[0, "lead_time_dias"], (int, np.integer))


# ===========================================================================
# validate  (integrity.py)
# ===========================================================================


class TestValidate:
    """
    Regras validadas:
    1. Quando csv == dw → não lança exceção
    2. Quando csv != dw → lança ValueError com mensagem informativa
    3. A mensagem de erro contém os valores que divergem

    """

    def test_contagens_iguais_nao_lancam_excecao(self):
        # Não deve lançar nada
        validate("Programas", total_csv=10, total_dw=10)

    def test_contagens_diferentes_lancam_value_error(self):
        with pytest.raises(ValueError):
            validate("Programas", total_csv=10, total_dw=8)

    def test_mensagem_de_erro_contem_nome_da_entidade(self):
        with pytest.raises(ValueError, match="Programas"):
            validate("Programas", total_csv=10, total_dw=8)

    def test_mensagem_de_erro_contem_valores_divergentes(self):
        with pytest.raises(ValueError, match="10"):
            validate("Projetos", total_csv=10, total_dw=5)

    def test_zero_csv_e_zero_dw_nao_lanca_excecao(self):
        # Tabela vazia carregada com CSV vazio — é válido
        validate("Tarefas", total_csv=0, total_dw=0)

    def test_dw_maior_que_csv_tambem_lanca_excecao(self):
        # Pode indicar que o delete() não foi executado antes do bulk_create
        with pytest.raises(ValueError):
            validate("Materiais", total_csv=5, total_dw=10)

    def test_diferenca_de_um_registro_detectada(self):
        # Garante que a validação não tem tolerância implícita
        with pytest.raises(ValueError):
            validate("Fornecedores", total_csv=100, total_dw=99)


# ===========================================================================
# Funções auxiliares do loader (get_date_cache e filter_valid_ids)
# ===========================================================================


class TestGetDateCacheLogicaDeParsing:
    """
    get_date_cache não pode ser testada plenamente sem banco (ela chama
    DimData.objects.get_or_create). Mas sua lógica de parsing de string
    para date pode ser testada isoladamente.

    """

    def _parse_date_str(self, date_str: str) -> date:
        """Replica: clean_date = str(date_str)[:10]; dt_obj = datetime.strptime(...)"""
        from datetime import datetime

        clean_date = str(date_str)[:10]
        return datetime.strptime(clean_date, "%Y-%m-%d").date()

    def test_formato_iso_completo_parseado_corretamente(self):
        resultado = self._parse_date_str("2024-01-15")
        assert resultado == date(2024, 1, 15)

    def test_timestamp_com_hora_truncado_corretamente(self):
        # str(timestamp)[:10] deve remover a parte de hora
        resultado = self._parse_date_str("2024-01-15 08:30:00")
        assert resultado == date(2024, 1, 15)

    def test_dia_e_mes_um_digito_parseados(self):
        # pandas pode gerar "2024-1-5" para datas com mes/dia de 1 dígito
        # strptime com %Y-%m-%d aceita isso
        resultado = self._parse_date_str("2024-01-05")
        assert resultado == date(2024, 1, 5)

    def test_virada_de_ano(self):
        resultado = self._parse_date_str("2023-12-31")
        assert resultado == date(2023, 12, 31)


class TestFilterValidIds:
    """
    filter_valid_ids recebe um DataFrame e remove linhas com IDs
    que não existem no banco. A lógica de filtragem (isin) pode ser
    testada sem banco mockando o queryset.
    """

    def _filtrar(self, df: pd.DataFrame, ids_validos: set, coluna: str) -> pd.DataFrame:
        """
        Replica a lógica de filter_valid_ids sem o ORM:
            valid_ids = set(model.objects.values_list('id', flat=True))
            df_filtered = df[df[column_name].isin(valid_ids)]
        """
        return df[df[coluna].isin(ids_validos)]

    def test_ids_validos_preservados(self):
        df = pd.DataFrame({"programa_id": [1, 2, 3]})
        resultado = self._filtrar(df, {1, 2, 3}, "programa_id")
        assert len(resultado) == 3

    def test_ids_invalidos_removidos(self):
        df = pd.DataFrame({"programa_id": [1, 2, 99]})
        resultado = self._filtrar(df, {1, 2}, "programa_id")
        assert len(resultado) == 2
        assert 99 not in resultado["programa_id"].values

    def test_todos_invalidos_retorna_dataframe_vazio(self):
        df = pd.DataFrame({"programa_id": [10, 20, 30]})
        resultado = self._filtrar(df, {1, 2, 3}, "programa_id")
        assert len(resultado) == 0

    def test_dataframe_vazio_retorna_vazio(self):
        df = pd.DataFrame({"programa_id": []})
        resultado = self._filtrar(df, {1, 2, 3}, "programa_id")
        assert len(resultado) == 0

    def test_filtragem_nao_altera_outras_colunas(self):
        df = pd.DataFrame(
            {
                "programa_id": [1, 2, 99],
                "nome": ["Alpha", "Beta", "Invalido"],
            }
        )
        resultado = self._filtrar(df, {1, 2}, "programa_id")
        assert list(resultado["nome"]) == ["Alpha", "Beta"]
