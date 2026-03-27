from rest_framework import serializers
from .models import FatoEmpenho

class EmpenhoSerializer(serializers.ModelSerializer):
    material = serializers.CharField(source='material.descricao')
    categoria = serializers.CharField(source='material.categoria')
    data = serializers.SerializerMethodField()
    custo_total = serializers.SerializerMethodField()

    class Meta:
        model = FatoEmpenho
        fields = [
            'id',
            'material',
            'categoria',
            'quantidade_empenhada',
            'data',
            'custo_total'
        ]

    def get_data(self, obj):
        return f"{obj.data_empenho.dia}/{obj.data_empenho.mes}/{obj.data_empenho.ano}"

    def get_custo_total(self, obj):
        return obj.quantidade_empenhada * obj.material.custo_estimado