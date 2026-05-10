import pandas as pd
import numpy as np
from datetime import datetime
import unicodedata

def remove_accents(input_str):
    """Remove acentos de uma string e padroniza para comparação."""
    if not isinstance(input_str, str):
        return input_str
    #normaliza para decompor caracteres acentuados e remove os fragmentos de acento
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def standardize_strings(df, columns):
    """Remove espaços, acentos e padroniza para caixa alta."""
    for col in columns:
        if col in df.columns:
            #padroniza: limpa espaços, remove acentos e coloca em maiúsculo
            df[col] = df[col].astype(str).str.strip().apply(remove_accents).str.upper()
            
            # substitui strings que representam nulos por um valor padrão
            df[col] = df[col].replace(['NAN', 'NONE', 'NAT', 'NULL', ''], 'NAO INFORMADO')
    return df

def handle_nulls(df):
    """Trata valores nulos em colunas numéricas e de data."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    return df

def calculate_project_metrics(df):
    """
    Função principal que utiliza as funções auxiliares para transformar o DataFrame.
    """
    if df.empty:
        return df

    df = standardize_strings(df, ['status', 'nome', 'responsavel'])
    df = handle_nulls(df)

    df['data_inicio'] = pd.to_datetime(df['data_inicio'], errors='coerce')
    df['data_fim_prevista'] = pd.to_datetime(df['data_fim_prevista'], errors='coerce')

    # 1. Cálculo de lead_time_dias (diferença entre fim previsto e início)
    df['lead_time_dias'] = (df['data_fim_prevista'] - df['data_inicio']).dt.days.fillna(0).astype(int)

    # 2. Cálculo de is_atrasado (com base na data prevista e status)
    hoje = pd.Timestamp(datetime.now().date())
    
    #primeiro, garantimos que o status está padronizado para a comparação
    if 'status' in df.columns:
        #criamos uma série temporária padronizada para a verificação
        status_clean = df['status'].astype(str).str.strip().apply(remove_accents).str.upper()
        
        #regra: Está atrasado SE (data prevista < hoje) E (status NÃO É concluído)
        df['is_atrasado'] = (df['data_fim_prevista'] < hoje) & (status_clean != 'CONCLUIDO')
    else:
        #caso a coluna status não exista (fallback de segurança)
        df['is_atrasado'] = df['data_fim_prevista'] < hoje
            
    #garante que valores nulos em datas não resultem em atraso True
    df['is_atrasado'] = df['is_atrasado'].fillna(False)

    return df


def calculate_estoque_saldo(df_estoque, df_solicitacoes, df_materiais, df_pedidos):
    """
    Calcula os campos da FatoEstoqueSaldo:
    - quantidade_disponivel: soma(valor_total dos pedidos / custo_estimado do material)
    - valor_total: soma(valor_total dos pedidos) - (soma(qtd_solicitada) × custo_estimado)
    - data_ultima_atualizacao: data do último pedido com status 'Entregue'
    """
    if df_estoque.empty:
        return df_estoque

    # Juntar pedidos com solicitações para obter material_id
    df_ped_sol = df_pedidos.merge(
        df_solicitacoes[['id', 'material_id', 'quantidade']],
        left_on='solicitacao_id', right_on='id', suffixes=('', '_sol')
    )

    # Agrupar por material_id: soma valor_total e qtd_solicitada
    agg = df_ped_sol.groupby('material_id').agg(
        valor_total_pedidos=('valor_total', 'sum'),
        qtd_solicitada_total=('quantidade', 'sum')
    ).reset_index()

    # Data última atualização: apenas pedidos Entregue
    df_entregues = df_ped_sol[df_ped_sol['status'].str.strip().str.upper() == 'ENTREGUE']
    if not df_entregues.empty:
        agg_datas = df_entregues.groupby('material_id').agg(data_ultima=('data_pedido', 'max')).reset_index()
    else:
        agg_datas = pd.DataFrame(columns=['material_id', 'data_ultima'])

    # Montar resultado: estoque + custo do material + agregações
    df_result = df_estoque.merge(df_materiais[['id', 'custo_estimado']], left_on='material_id', right_on='id', suffixes=('', '_mat'))
    df_result = df_result.merge(agg, on='material_id', how='left')
    df_result = df_result.merge(agg_datas, on='material_id', how='left')

    # Só manter materiais que têm pelo menos um pedido Entregue
    df_result = df_result.dropna(subset=['data_ultima'])

    # Calcular campos
    df_result['quantidade_disponivel'] = df_result.apply(
        lambda r: int(r['valor_total_pedidos'] / r['custo_estimado']) if r['custo_estimado'] > 0 else 0, axis=1
    )
    df_result['valor_total'] = df_result['valor_total_pedidos'] - (df_result['qtd_solicitada_total'] * df_result['custo_estimado'])
    df_result['data_ultima_atualizacao'] = df_result['data_ultima']

    return df_result