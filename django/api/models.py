from django.db import models
from django.db.models import FloatField, ForeignKey, IntegerField, CharField, DecimalField, CASCADE

class DimData(models.Model):
    dia = IntegerField() 
    mes = IntegerField()
    ano = IntegerField()
# '''CREATE TABLE dim_data (
#     id INT PRIMARY KEY,
#     dia INT NOT NULL,
#     mes INT NOT NULL,
#     ano INT NOT NULL
# )''',

class DimPrograma(models.Model):
    codigo_programa = CharField()
    nome_programa = CharField()
    gerente_programa = CharField()
    gerente_tecnico = CharField()
    data_inicio = ForeignKey(DimData, on_delete=CASCADE, related_name='programa_data_inicio')
    data_fim_prevista = ForeignKey(DimData, on_delete=CASCADE, related_name='programa_data_fim_prevista')
    status = CharField()
    
# '''CREATE TABLE dim_programa (
#     id VARCHAR(50) PRIMARY KEY,
#     codigo_programa VARCHAR(50),
#     nome_programa VARCHAR(100),
#     gerente_programa VARCHAR(100),
#     gerente_tecnico VARCHAR(100),
#     data_inicio INT REFERENCES dim_data(id),
#     data_fim_prevista INT REFERENCES dim_data(id),
#     status VARCHAR(50)
# )''',

class DimProjeto(models.Model):
    codigo_projeto = CharField()
    nome_projeto = CharField()
    programa = ForeignKey(DimPrograma, on_delete=CASCADE)
    responsavel = CharField()
    custo_hora = DecimalField(max_digits=10, decimal_places=2)
    data_inicio = ForeignKey(DimData, on_delete=CASCADE, related_name='projeto_data_inicio')
    data_fim_prevista = ForeignKey(DimData, on_delete=CASCADE, related_name='projeto_data_fim_prevista')
    status = CharField()
#
# '''CREATE TABLE dim_projeto (
#     id VARCHAR(50) PRIMARY KEY,
#     codigo_projeto VARCHAR(50),
#     nome_projeto VARCHAR(100),
#     programa_id VARCHAR(50) REFERENCES dim_programa(id),
#     responsavel VARCHAR(100),
#     custo_hora VARCHAR(50),
#     data_inicio INT REFERENCES dim_data(id),
#     data_fim_prevista INT REFERENCES dim_data(id),
#     status VARCHAR(50)
# )''',

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
# '''CREATE TABLE dim_tarefa (
#     id INT PRIMARY KEY,
#     codigo_tarefa VARCHAR(50),
#     projeto_id VARCHAR(50) REFERENCES dim_projeto(id),
#     titulo VARCHAR(200),
#     responsavel VARCHAR(100),
#     estimativa VARCHAR(50),
#     data_inicio INT REFERENCES dim_data(id),
#     data_fim_prevista INT REFERENCES dim_data(id),
#     status VARCHAR(50)
# )''',
#
class DimMaterial(models.Model):
    codigo_material = CharField()
    descricao = CharField()
    categoria = CharField()
    fabricante = CharField()
    custo_estimado = DecimalField(max_digits=10, decimal_places=2)
    status = CharField()
# '''CREATE TABLE dim_material (
#     id VARCHAR(50) PRIMARY KEY,
#     codigo_material VARCHAR(50),
#     descricao VARCHAR(200),
#     categoria VARCHAR(100),
#     fabricante VARCHAR(100),
#     custo_estimado VARCHAR(50),
#     status VARCHAR(50)
# )''',
#
class DimFornecedor(models.Model):
    codigo_fornecedor = CharField()
    razao_social = CharField()
    cidade = CharField()
    estado = CharField()
    categoria = CharField()
    status = CharField()
# '''CREATE TABLE dim_fornecedor (
#     id VARCHAR(50) PRIMARY KEY,
#     codigo_fornecedor VARCHAR(50),
#     razao_social VARCHAR(200),
#     cidade VARCHAR(100),
#     estado VARCHAR(50),
#     categoria VARCHAR(100),
#     status VARCHAR(50)
# )''',
#
class DimSolicitacao(models.Model):
    numero_solicitacao = CharField(max_length=6)
    projeto = ForeignKey(DimProjeto, on_delete=CASCADE)
    material = ForeignKey(DimMaterial, on_delete=CASCADE)
    quantidade = IntegerField()
    data_solicitacao = ForeignKey(DimData, on_delete=CASCADE)
    prioridade = CharField()
    status = CharField()
# '''CREATE TABLE dim_solicitacao (
#     id VARCHAR(50) PRIMARY KEY,
#     numero_solicitacao VARCHAR(50),
#     projeto_id VARCHAR(50) REFERENCES dim_projeto(id),
#     material_id VARCHAR(50) REFERENCES dim_material(id),
#     quantidade VARCHAR(50),
#     data_solicitacao VARCHAR(50),
#     prioridade VARCHAR(50),
#     status VARCHAR(50)
# )''',
#
#
class FatoTarefa(models.Model):
    usuario = CharField()
    horas_trabalhadas = FloatField()
    tarefa = ForeignKey(DimTarefa, on_delete=CASCADE)
    data = ForeignKey(DimData, on_delete=CASCADE)
# '''CREATE TABLE fato_tarefa (
#     id INT PRIMARY KEY,
#     usuario VARCHAR(100),
#     horas_trabalhadas FLOAT,
#     tarefa_id INT REFERENCES dim_tarefa(id),
#     data INT REFERENCES dim_data(id)
# )''',
#
class FatoEmpenho(models.Model):
    quantidade_empenhada = IntegerField()
    projeto = ForeignKey(DimProjeto, on_delete=CASCADE)
    material = ForeignKey(DimMaterial, on_delete=CASCADE)
    data_empenho = ForeignKey(DimData, on_delete=CASCADE)
# '''CREATE TABLE fato_empenho (
#     id VARCHAR(50) PRIMARY KEY,
#     quantidade_empenhada INT,
#     projeto_id VARCHAR(50) REFERENCES dim_projeto(id),
#     material_id VARCHAR(50) REFERENCES dim_material(id),
#     data_empenho INT REFERENCES dim_data(id)
# )''',
#
class FatoCompra(models.Model):
    numero_pedido = CharField(unique=True)
    valor_total = DecimalField(max_digits=10, decimal_places=2)
    status = CharField()
    solicitacao = ForeignKey(DimSolicitacao, on_delete=CASCADE)
    fornecedor = ForeignKey(DimFornecedor, on_delete=CASCADE)
    data_pedido = ForeignKey(DimData, on_delete=CASCADE, related_name='compra_data_pedido')
    data_previsao_entrega = ForeignKey(DimData, on_delete=CASCADE, related_name='compra_data_previsao_entrega')
# '''CREATE TABLE fato_compra (
#     id INT PRIMARY KEY,
#     numero_pedido VARCHAR(50) UNIQUE,
#     valor_total FLOAT,
#     status VARCHAR(50),
#     solicitacao_id VARCHAR(50) REFERENCES dim_solicitacao(id),
#     fornecedor_id VARCHAR(50) REFERENCES dim_fornecedor(id),
#     data_pedido INT REFERENCES dim_data(id),
#     data_previsao_entrega INT REFERENCES dim_data(id)
# )'''
