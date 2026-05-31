from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from etl.extractors.csv_extractor import extrair_csv
from etl.validators.csv_validator import validar_csv
from etl.transformations.csv_transformer import transformar_csv
from etl.loaders.csv_loader import carregar_csv

@csrf_exempt
@require_POST
def importar_dados_api(request):

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

        df = extrair_csv(arquivo)

        tipo_csv = validar_csv(df)

        df_transformado = transformar_csv(
            df,
            tipo_csv
        )

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

    except ValueError as e:

        return JsonResponse(
            {
                "erro": str(e)
            },
            status=400
        )