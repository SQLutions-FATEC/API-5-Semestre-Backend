from django.db import models
from django.db.models import FloatField, ForeignKey, IntegerField, CharField, DecimalField, CASCADE

class DimData(models.Model):
    dia = IntegerField() 
    mes = IntegerField()
    ano = IntegerField()

class DimPrograma(models.Model):
    codigo_programa = CharField()
    nome_programa = CharField()
    gerente_programa = CharField()
    gerente_tecnico = CharField()
    data_inicio = ForeignKey(DimData, on_delete=CASCADE, related_name='programa_data_inicio')
    data_fim_prevista = ForeignKey(DimData, on_delete=CASCADE, related_name='programa_data_fim_prevista')
    status = CharField()

class DimProjeto(models.Model):
    codigo_projeto = CharField()
    nome_projeto = CharField()
    programa = ForeignKey(DimPrograma, on_delete=CASCADE)
    responsavel = CharField()
    custo_hora = DecimalField(max_digits=10, decimal_places=2)
    data_inicio = ForeignKey(DimData, on_delete=CASCADE, related_name='projeto_data_inicio')
    data_fim_prevista = ForeignKey(DimData, on_delete=CASCADE, related_name='projeto_data_fim_prevista')
    status = CharField()

class DimTarefa(models.Model):
    codigo_tarefa = CharField(max_length=6)
    projeto = ForeignKey(DimProjeto, on_delete=CASCADE)
    titulo = CharField()
    titulo = CharField()
    responsavel = CharField()
    estimativa = IntegerField()
    data_inicio = ForeignKey(DimData, on_delete=CASCADE, related_name='tarefa_data_inicio')
    data_fim_prevista = ForeignKey(DimData, on_delete=CASCADE, related_name='tarefa_data_fim_prevista')
    status = CharField()

class DimMaterial(models.Model):
    codigo_material = CharField()
    descricao = CharField()
    categoria = CharField()
    fabricante = CharField()
    custo_estimado = DecimalField(max_digits=10, decimal_places=2)
    status = CharField()

class DimFornecedor(models.Model):
    codigo_fornecedor = CharField()
    razao_social = CharField()
    cidade = CharField()
    estado = CharField()
    categoria = CharField()
    status = CharField()

class DimSolicitacao(models.Model):
    numero_solicitacao = CharField(max_length=6)
    projeto = ForeignKey(DimProjeto, on_delete=CASCADE)
    material = ForeignKey(DimMaterial, on_delete=CASCADE)
    quantidade = IntegerField()
    data_solicitacao = ForeignKey(DimData, on_delete=CASCADE)
    prioridade = CharField()
    status = CharField()

class FatoTarefa(models.Model):
    usuario = CharField()
    horas_trabalhadas = FloatField()
    tarefa = ForeignKey(DimTarefa, on_delete=CASCADE)
    data = ForeignKey(DimData, on_delete=CASCADE)

class FatoEmpenho(models.Model):
    quantidade_empenhada = IntegerField()
    projeto = ForeignKey(DimProjeto, on_delete=CASCADE)
    material = ForeignKey(DimMaterial, on_delete=CASCADE)
    data_empenho = ForeignKey(DimData, on_delete=CASCADE)

class FatoCompra(models.Model):
    numero_pedido = CharField(unique=True)
    valor_total = DecimalField(max_digits=10, decimal_places=2)
    status = CharField()
    solicitacao = ForeignKey(DimSolicitacao, on_delete=CASCADE)
    fornecedor = ForeignKey(DimFornecedor, on_delete=CASCADE)
    data_pedido = ForeignKey(DimData, on_delete=CASCADE, related_name='compra_data_pedido')
    data_previsao_entrega = ForeignKey(DimData, on_delete=CASCADE, related_name='compra_data_previsao_entrega')
