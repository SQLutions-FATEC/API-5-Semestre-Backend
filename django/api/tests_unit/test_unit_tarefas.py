"""
Testes unitários para tarefas.py.

Duas lógicas testadas de forma isolada:

1. serializar_tarefa — a list comprehension que monta o dict por tarefa,
   incluindo o padrão `round(float(... or 0.0), 2)` para horas.

2. montar_evolucao_horas — o dict comprehension que formata as chaves
   de data como 'YYYY-MM-DD' e aplica round() nos valores.

"""

import pytest


# ---------------------------------------------------------------------------
# Fórmulas replicadas da view
# ---------------------------------------------------------------------------

def serializar_tarefa(tarefa: dict) -> dict:
    """
    Replica o corpo da list comprehension de projeto_tarefas_timesheet_api:

        tarefas = [
            {
                'codigo': tarefa['codigo_tarefa'],
                'titulo': tarefa['titulo'],
                'responsavel': tarefa['responsavel'],
                'estimativa': tarefa['estimativa'],
                'status': tarefa['status'],
                'total_horas_trabalhadas': round(float(tarefa['total_horas_trabalhadas'] or 0.0), 2),
            }
            for tarefa in tarefas_qs
        ]

    """
    return {
        "codigo": tarefa["codigo_tarefa"],
        "titulo": tarefa["titulo"],
        "responsavel": tarefa["responsavel"],
        "estimativa": tarefa["estimativa"],
        "status": tarefa["status"],
        "total_horas_trabalhadas": round(float(tarefa["total_horas_trabalhadas"] or 0.0), 2),
    }


def montar_evolucao_horas(evolucao_qs: list[dict]) -> dict:
    """
    Replica o dict comprehension de evolucao_horas:

        evolucao_horas = {
            f"{item['data__ano']:04d}-{item['data__mes']:02d}-{item['data__dia']:02d}":
                round(float(item['total_horas'] or 0.0), 2)
            for item in evolucao_qs
        }

    Recebe uma lista de dicts simulando o retorno do
    .values().annotate() do ORM e retorna o dict {data_str: horas}.
    """
    return {
        f"{item['data__ano']:04d}-{item['data__mes']:02d}-{item['data__dia']:02d}":
            round(float(item["total_horas"] or 0.0), 2)
        for item in evolucao_qs
    }


# ---------------------------------------------------------------------------
# Helpers — fábricas de dicts que simulam retorno do ORM
# ---------------------------------------------------------------------------

def make_tarefa_orm(
    codigo_tarefa="TS01",
    titulo="Planejamento",
    responsavel="Ana",
    estimativa=8,
    status="Ativo",
    total_horas_trabalhadas=4.0,
):
    """Simula um item retornado por .values() na queryset de tarefas."""
    return {
        "codigo_tarefa": codigo_tarefa,
        "titulo": titulo,
        "responsavel": responsavel,
        "estimativa": estimativa,
        "status": status,
        "total_horas_trabalhadas": total_horas_trabalhadas,
    }


def make_evolucao_item(
    ano=2024, mes=1, dia=1,
    total_horas=2.25,
):
    """Simula um item retornado por .values().annotate() na queryset de evolução."""
    return {
        "data__ano": ano,
        "data__mes": mes,
        "data__dia": dia,
        "total_horas": total_horas,
    }


# ===========================================================================
# serializar_tarefa
# ===========================================================================

class TestSerializarTarefa:
    """
    Regras validadas:
    1. Todos os campos esperados estão presentes e mapeados corretamente
    2. 'codigo' vem de 'codigo_tarefa' (mapeamento não-trivial)
    3. total_horas_trabalhadas None retorna 0.0 (fallback)
    4. total_horas_trabalhadas é arredondado a 2 casas decimais
    5. Cenários exatos de test_tarefas.py (TS01: 4.0h, TS02: 3.0h)
    """

    def test_todos_os_campos_presentes(self):
        tarefa = make_tarefa_orm()
        resultado = serializar_tarefa(tarefa)

        assert "codigo" in resultado
        assert "titulo" in resultado
        assert "responsavel" in resultado
        assert "estimativa" in resultado
        assert "status" in resultado
        assert "total_horas_trabalhadas" in resultado

    def test_campo_codigo_vem_de_codigo_tarefa(self):
        # Mapeamento não-óbvio: chave 'codigo_tarefa' no ORM → 'codigo' no JSON
        tarefa = make_tarefa_orm(codigo_tarefa="TS01")
        resultado = serializar_tarefa(tarefa)
        assert resultado["codigo"] == "TS01"

    def test_chave_codigo_tarefa_nao_exposta_no_json(self):
        # A view renomeia a chave — 'codigo_tarefa' não deve aparecer no response
        tarefa = make_tarefa_orm()
        resultado = serializar_tarefa(tarefa)
        assert "codigo_tarefa" not in resultado

    def test_total_horas_none_retorna_zero(self):
        # Tarefa sem apontamentos: total_horas_trabalhadas é None no ORM
        # (cenário de tarefa_sem_apontamento em test_dashboard.py)
        tarefa = make_tarefa_orm(total_horas_trabalhadas=None)
        resultado = serializar_tarefa(tarefa)
        assert resultado["total_horas_trabalhadas"] == 0.0

    def test_total_horas_arredondado_a_dois_decimais(self):
        tarefa = make_tarefa_orm(total_horas_trabalhadas=4.556)
        resultado = serializar_tarefa(tarefa)
        assert resultado["total_horas_trabalhadas"] == 4.56

    def test_total_horas_preserva_valor_exato_quando_sem_arredondamento(self):
        tarefa = make_tarefa_orm(total_horas_trabalhadas=4.0)
        resultado = serializar_tarefa(tarefa)
        assert resultado["total_horas_trabalhadas"] == 4.0

    def test_cenario_ts01_do_teste_de_integracao(self):
        # TS01: ana (2.25h dia 1) + ana (1.75h dia 2) = 4.0h total
        tarefa = make_tarefa_orm(
            codigo_tarefa="TS01",
            titulo="Planejamento",
            responsavel="Ana",
            estimativa=8,
            status="Ativo",
            total_horas_trabalhadas=4.0,
        )
        resultado = serializar_tarefa(tarefa)
        assert resultado["codigo"] == "TS01"
        assert resultado["total_horas_trabalhadas"] == 4.0

    def test_cenario_ts02_do_teste_de_integracao(self):
        # TS02: bruno (3.0h dia 2) = 3.0h total
        tarefa = make_tarefa_orm(
            codigo_tarefa="TS02",
            titulo="Execucao",
            responsavel="Bruno",
            estimativa=16,
            status="Ativo",
            total_horas_trabalhadas=3.0,
        )
        resultado = serializar_tarefa(tarefa)
        assert resultado["codigo"] == "TS02"
        assert resultado["total_horas_trabalhadas"] == 3.0

    def test_estimativa_preservada_como_inteiro(self):
        tarefa = make_tarefa_orm(estimativa=16)
        resultado = serializar_tarefa(tarefa)
        assert resultado["estimativa"] == 16


# ===========================================================================
# montar_evolucao_horas
# ===========================================================================

class TestMontarEvolucaoHoras:
    """
    Regras validadas:
    1. Chave de data formatada como 'YYYY-MM-DD' com zeros à esquerda
    2. Horas arredondadas a 2 casas decimais
    3. total_horas None retorna 0.0 para aquela data
    4. Múltiplos dias geram múltiplas chaves
    5. Cenários exatos de test_tarefas.py (2024-01-01 e 2024-01-02)
    """

    def test_formato_data_com_zeros_a_esquerda(self):
        # mes=1, dia=1 → "2024-01-01" (não "2024-1-1")
        entrada = [make_evolucao_item(ano=2024, mes=1, dia=1)]
        resultado = montar_evolucao_horas(entrada)
        assert "2024-01-01" in resultado

    def test_formato_data_mes_e_dia_dois_digitos(self):
        entrada = [make_evolucao_item(ano=2024, mes=12, dia=31)]
        resultado = montar_evolucao_horas(entrada)
        assert "2024-12-31" in resultado

    def test_horas_arredondadas_a_dois_decimais(self):
        entrada = [make_evolucao_item(total_horas=2.2567)]
        resultado = montar_evolucao_horas(entrada)
        assert resultado["2024-01-01"] == 2.26

    def test_total_horas_none_retorna_zero(self):
        entrada = [make_evolucao_item(total_horas=None)]
        resultado = montar_evolucao_horas(entrada)
        assert resultado["2024-01-01"] == 0.0

    def test_multiplos_dias_geram_multiplas_chaves(self):
        entrada = [
            make_evolucao_item(ano=2024, mes=1, dia=1, total_horas=2.25),
            make_evolucao_item(ano=2024, mes=1, dia=2, total_horas=4.75),
        ]
        resultado = montar_evolucao_horas(entrada)
        assert len(resultado) == 2

    def test_cenario_exato_dia1_do_teste_de_integracao(self):
        # 2024-01-01: só ana com 2.25h
        entrada = [make_evolucao_item(ano=2024, mes=1, dia=1, total_horas=2.25)]
        resultado = montar_evolucao_horas(entrada)
        assert resultado["2024-01-01"] == 2.25

    def test_cenario_exato_dia2_do_teste_de_integracao(self):
        # 2024-01-02: ana (1.75h) + bruno (3.0h) = 4.75h
        entrada = [make_evolucao_item(ano=2024, mes=1, dia=2, total_horas=4.75)]
        resultado = montar_evolucao_horas(entrada)
        assert resultado["2024-01-02"] == 4.75

    def test_lista_vazia_retorna_dict_vazio(self):
        assert montar_evolucao_horas([]) == {}

    def test_valores_sao_float(self):
        entrada = [make_evolucao_item(total_horas=3.0)]
        resultado = montar_evolucao_horas(entrada)
        assert isinstance(resultado["2024-01-01"], float)