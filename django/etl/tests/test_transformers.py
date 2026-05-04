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

def test_calculate_estoque_saldo_logic():
    """
    Testa a lógica de saldo de estoque:
    - Quantidade disponível (valor_total_pedidos / custo_estimado)
    - Valor total (valor_total_pedidos - qtd_solicitada * custo_estimado)
    - Filtro de pedidos 'ENTREGUE'
    """
    from etl.transformations.transformers import calculate_estoque_saldo

    # 1. Mocks de entrada
    df_estoque = pd.DataFrame({
        'material_id': [1, 2],
        'projeto_id': [10, 20],
        'localizacao': ['LOC A', 'LOC B']
    })
    
    df_materiais = pd.DataFrame({
        'id': [1, 2],
        'custo_estimado': [100.0, 50.0]
    })
    
    df_solicitacoes = pd.DataFrame({
        'id': [101, 102],
        'material_id': [1, 2],
        'quantidade': [10, 5]
    })
    
    df_pedidos = pd.DataFrame({
        'solicitacao_id': [101, 102],
        'valor_total': [1000.0, 500.0],
        'status': ['ENTREGUE', 'PENDENTE'], # Apenas material 1 deve passar no filtro final
        'data_pedido': ['2023-01-01', '2023-01-02']
    })

    # 2. Execução
    result_df = calculate_estoque_saldo(df_estoque, df_solicitacoes, df_materiais, df_pedidos)

    # 3. Asserts
    # Apenas material 1 deve existir no resultado (porque material 2 não está 'ENTREGUE')
    assert len(result_df) == 1
    assert result_df.iloc[0]['material_id'] == 1
    
    # Qtd disponível: 1000 / 100 = 10
    assert result_df.iloc[0]['quantidade_disponivel'] == 10
    
    # Valor total: 1000 - (10 * 100) = 0
    assert result_df.iloc[0]['valor_total'] == 0
    
    # Data última atualização
    assert result_df.iloc[0]['data_ultima_atualizacao'] == '2023-01-01'