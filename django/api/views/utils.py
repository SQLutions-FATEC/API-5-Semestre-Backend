import unicodedata
from datetime import date
from django.shortcuts import get_object_or_404
from api.models import DimProjeto

def obter_projeto(codigo_projeto):
    """Evita repetir o get_object_or_404 em todas as views"""
    return get_object_or_404(DimProjeto, codigo_projeto=codigo_projeto)

def formatar_data_dim(dim_data):
    """Padroniza a formatação de datas YYYY-MM-DD vindo da dimensão tempo"""
    if dim_data is None:
        return None
    try:
        return f"{dim_data.ano:04d}-{dim_data.mes:02d}-{dim_data.dia:02d}"
    except AttributeError:
        return None

def _normaliza_texto(valor):
    if valor is None:
        return ''
    texto_sem_acentos = unicodedata.normalize('NFKD', str(valor)).encode('ASCII', 'ignore').decode('ASCII')
    return texto_sem_acentos.strip().lower()

def _dim_data_para_date(dim_data):
    if dim_data is None:
        return None
    try:
        return date(dim_data.ano, dim_data.mes, dim_data.dia)
    except (TypeError, ValueError):
        return None