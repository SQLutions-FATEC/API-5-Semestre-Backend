import pytest
import pandas as pd
from etl.transformations.transformers import calculate_project_metrics

@pytest.mark.django_db
def test_calculate_project_metrics_logic():
    """
    Testa a lógica de cálculo de lead time e a flag de atraso.
    Garante a cobertura de código para a Task 17.
    """
    #dados de teste: Projeto 0 (no prazo/concluído) e Projeto 1 (atrasado)
    data = {
        'data_inicio': ['2023-01-01', '2023-01-01'],
        'data_fim_prevista': ['2023-01-11', '2023-01-05'],
        'status': ['CONCLUIDO', 'EM ANDAMENTO']
    }
    df = pd.DataFrame(data)

    #execução da função de transformação
    result_df = calculate_project_metrics(df)

    #asserts para validar os calculos
    #projeto 0: 11 - 1 = 10 dias de lead time
    assert result_df.loc[0, 'lead_time_dias'] == 10
    
    #projeto 1: Data de 2023 é anterior a hoje, status não é CONCLUIDO
    assert result_df.loc[1, 'is_atrasado'] == True