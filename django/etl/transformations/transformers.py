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
            
            #substitui strings que representam nulos por um valor padrão
            df[col] = df[col].replace(['NAN', 'NONE', 'NAT', 'NULL', ''], 'NAO INFORMADO')
    return df

def handle_nulls(df):
    """Trata valores nulos em colunas numéricas e de data."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)
    return df
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
            #nota: Usamos 'CONCLUIDO' sem acento devido à função remove_accents
            df['is_atrasado'] = (df['data_fim_prevista'] < hoje) & (status_clean != 'CONCLUIDO')
        else:
            #caso a coluna status não exista (fallback de segurança)
            df['is_atrasado'] = df['data_fim_prevista'] < hoje
            
        #garante que valores nulos em datas não resultem em atraso True
        df['is_atrasado'] = df['is_atrasado'].fillna(False)

    return df