from django.db import models
from django.db.models import FloatField, ForeignKey, IntegerField, CharField, DecimalField, CASCADE

class DimData(models.Model):
    dia = IntegerField() 
    mes = IntegerField()
    ano = IntegerField()

class DimPrograma(models.Model):
    codigo_programa = CharField(max_length=10)
    nome_programa = CharField(max_length=256)
    gerente_programa = CharField(max_length=256)
    gerente_tecnico = CharField(max_length=256)
    data_inicio = ForeignKey(DimData, on_delete=CASCADE, related_name='programa_data_inicio')
    data_fim_prevista = ForeignKey(DimData, on_delete=CASCADE, related_name='programa_data_fim_prevista')
    status = CharField(max_length=30)

class DimProjeto(models.Model):
    codigo_projeto = CharField(max_length=6)
    nome_projeto = CharField(max_length=256)
    programa = ForeignKey(DimPrograma, on_delete=CASCADE)
    responsavel = CharField(max_length=256)
    custo_hora = DecimalField(max_digits=10, decimal_places=2)
    data_inicio = ForeignKey(DimData, on_delete=CASCADE, related_name='projeto_data_inicio')
    data_fim_prevista = ForeignKey(DimData, on_delete=CASCADE, related_name='projeto_data_fim_prevista')
    status = CharField(max_length=30)
    lead_time_dias = IntegerField(default=0)
    is_atrasado = models.BooleanField(default=False)

class DimTarefa(models.Model):
    codigo_tarefa = CharField(max_length=6)
    projeto = ForeignKey(DimProjeto, on_delete=CASCADE)
    titulo = CharField(max_length=256)
    titulo = CharField(max_length=256)
    responsavel = CharField(max_length=256)
    estimativa = IntegerField()
    data_inicio = ForeignKey(DimData, on_delete=CASCADE, related_name='tarefa_data_inicio')
    data_fim_prevista = ForeignKey(DimData, on_delete=CASCADE, related_name='tarefa_data_fim_prevista')
    status = CharField(max_length=30)
    lead_time_dias = IntegerField(default=0)
    is_atrasado = models.BooleanField(default=False)

class DimMaterial(models.Model):
    codigo_material = CharField(max_length=6)
    descricao = CharField(max_length=256)
    categoria = CharField(max_length=256)
    fabricante = CharField(max_length=256)
    custo_estimado = DecimalField(max_digits=10, decimal_places=2)
    status = CharField(max_length=256)

class DimFornecedor(models.Model):
    codigo_fornecedor = CharField(max_length=6)
    razao_social = CharField(max_length=256)
    cidade = CharField(max_length=256)
    estado = CharField(max_length=256)
    categoria = CharField(max_length=256)
    status = CharField(max_length=30)

class DimSolicitacao(models.Model):
    numero_solicitacao = CharField(max_length=6)
    projeto = ForeignKey(DimProjeto, on_delete=CASCADE)
    material = ForeignKey(DimMaterial, on_delete=CASCADE)
    quantidade = IntegerField()
    data_solicitacao = ForeignKey(DimData, on_delete=CASCADE)
    prioridade = CharField(max_length=20)
    status = CharField(max_length=30)

class FatoTarefa(models.Model):
    usuario = CharField(max_length=256)
    horas_trabalhadas = FloatField()
    tarefa = ForeignKey(DimTarefa, on_delete=CASCADE)
    data = ForeignKey(DimData, on_delete=CASCADE)

class FatoEmpenho(models.Model):
    quantidade_empenhada = IntegerField()
    projeto = ForeignKey(DimProjeto, on_delete=CASCADE)
    material = ForeignKey(DimMaterial, on_delete=CASCADE)
    data_empenho = ForeignKey(DimData, on_delete=CASCADE)

class FatoCompra(models.Model):
    numero_pedido = CharField(unique=True, max_length=6)
    valor_total = DecimalField(max_digits=10, decimal_places=2)
    status = CharField(max_length=30)
    solicitacao = ForeignKey(DimSolicitacao, on_delete=CASCADE)
    fornecedor = ForeignKey(DimFornecedor, on_delete=CASCADE)
    data_pedido = ForeignKey(DimData, on_delete=CASCADE, related_name='compra_data_pedido')
    data_previsao_entrega = ForeignKey(DimData, on_delete=CASCADE, related_name='compra_data_previsao_entrega')

class DimLocalizacao(models.Model):
    id_localizacao = CharField()
    localizacao = CharField()

class FatoEstoqueSaldo(models.Model):
    material = ForeignKey(DimMaterial, on_delete=CASCADE)
    projeto = ForeignKey(DimProjeto, on_delete=CASCADE)
    localizacao = ForeignKey(DimLocalizacao, on_delete=CASCADE)
    quantidade_disponivel = IntegerField()
    valor_total = DecimalField(max_digits=12, decimal_places=2)
    data_ultima_atualizacao = ForeignKey(DimData, on_delete=CASCADE)