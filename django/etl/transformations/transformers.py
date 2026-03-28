import pandas as pd
import numpy as np
from datetime import datetime

def standardize_strings(df, columns):
    """Remove espaços e padroniza para caixa alta."""
    for col in columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            #substitui strings que representam nulos por um valor padrão ou None
            df[col] = df[col].replace(['NAN', 'NONE', 'NAT', 'NULL', ''], 'NÃO INFORMADO')
    return df

def handle_nulls(df):
    """Trata valores nulos em colunas numéricas e de data."""
    #preenche valores numéricos nulos com 0 para não quebrar cálculos na dashboard
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    return df

def calculate_project_metrics(df):
    """Calcula lead_time_dias e is_atrasado para Projetos e Tarefas."""
    if 'data_inicio' in df.columns and 'data_fim_prevista' in df.columns:
        #garante que são objetos datetime
        df['data_inicio'] = pd.to_datetime(df['data_inicio'], errors='coerce')
        df['data_fim_prevista'] = pd.to_datetime(df['data_fim_prevista'], errors='coerce')
        
        # 1. cálculo de lead_time_dias (diferença entre fim previsto e início)
        df['lead_time_dias'] = (df['data_fim_prevista'] - df['data_inicio']).dt.days.fillna(0).astype(int)
        
        # 2. cálculo de is_atrasado (data atual vs previsão)
        hoje = pd.Timestamp(datetime.now().date())
        #regra: Se a data prevista é menor que hoje e não há status de 'CONCLUÍDO', está atrasado
        df['is_atrasado'] = df['data_fim_prevista'].apply(
            lambda x: x < hoje if pd.notnull(x) else False
        )
        
    return df