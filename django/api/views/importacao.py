import pandas as pd

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from etl.extractors.csv_extractor import extrair_csv
from etl.validators.csv_validator import validar_csv
from etl.transformations.csv_transformer import transformar_csv
from etl.loaders.csv_loader import carregar_csv


@require_POST
def importar_dados_api(request):

    print(request.FILES)
    print(request.POST)

    arquivo = request.FILES.get("file")

    if not arquivo:

        return JsonResponse(
            {
                "erro": "Arquivo não enviado"
            },
            status=400
        )

    if not arquivo.name.endswith(".csv"):

        return JsonResponse(
            {
                "erro": "Apenas arquivos CSV são permitidos"
            },
            status=400
        )

    try:

        # EXTRACT
        df = extrair_csv(arquivo)

        # VALIDATE
        tipo_csv = validar_csv(df)

        # TRANSFORM
        df_transformado = transformar_csv(
            df,
            tipo_csv
        )

        # LOAD
        carregar_csv(
            df_transformado,
            tipo_csv
        )

        return JsonResponse(
            {
                "mensagem": "Importação realizada com sucesso"
            },
            status=200
        )

    except Exception as e:

        return JsonResponse(
            {
                "erro": str(e)
            },
            status=400
        )