from datetime import date
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from api.models import DimSolicitacao
from .utils import obter_projeto, _dim_data_para_date

