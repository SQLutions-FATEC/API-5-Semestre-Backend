from rest_framework.views import APIView
from rest_framework.response import Response
from .models import FatoEmpenho
from .serializers import EmpenhoSerializer

class EmpenhoListView(APIView):

    def get(self, request):
        queryset = FatoEmpenho.objects.select_related(
            'material',
            'projeto',
            'data_empenho'
        )

        # 🔎 filtro por categoria
        categoria = request.GET.get('categoria')
        if categoria:
            queryset = queryset.filter(material__categoria=categoria)

        serializer = EmpenhoSerializer(queryset, many=True)
        return Response(serializer.data)