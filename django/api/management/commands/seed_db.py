import logging
from django.core.management.base import BaseCommand
from api.models import (
    DimData, DimPrograma, DimProjeto, DimTarefa, DimMaterial,
    DimFornecedor, DimSolicitacao, FatoTarefa, FatoEmpenho, FatoCompra
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Popula o Banco de Dados DW com dados mockados hardcoded para testes do frontend.'

    def handle(self, *args, **kwargs):
        dim_data_rows = [
            (1, 10, 1, 2022),
            (2, 20, 12, 2024),
            (3, 9, 5, 2022),
            (4, 27, 8, 2022),
            (5, 30, 4, 2025),
            (6, 15, 10, 2024),
            (7, 18, 5, 2024),
            (8, 25, 12, 2024),
            (9, 3, 11, 2024),
            (10, 11, 12, 2024),
            (11, 5, 2, 2023), 
            (12, 10, 8, 2023),
            (13, 20, 1, 2025),
            (14, 2, 2, 2025),
            (15, 15, 3, 2024),
            (16, 15, 10, 2026),
            (17, 5, 7, 2024),
            (18, 11, 1, 2025),
            (19, 14, 8, 2024),
            (20, 14, 10, 2024),
            (21, 10, 11, 2024),
            (22, 21, 11, 2024),
            (23, 23, 7, 2024),
            (24, 13, 10, 2024),
            (25, 11, 9, 2024),
            (26, 21, 11, 2024),
            (27, 7, 8, 2024),
            (28, 29, 8, 2024),
            (29, 1, 5, 2024),
            (30, 30, 1, 2027),
            (31, 31, 8, 2024),
            (32, 18, 5, 2025),
            (33, 1, 12, 2024),
            (34, 7, 1, 2025),
            (35, 12, 12, 2024),
            (36, 24, 12, 2024),
            (37, 3, 1, 2025),
            (38, 16, 2, 2025),
            (39, 8, 10, 2024),
            (40, 2, 3, 2025),
            (41, 23, 3, 2025)
        ]

        dim_programa_rows = [
            (1, 'MANSUP', 'MANSUP', 'Carlos Eduardo Martins', 'Rafael Carvalho', 1, 2, 'Concluído'),
            (2, 'MANSUP-ER', 'MANSUP-ER', 'Mariana Fernandes', 'Bruno Oliveira', 15, 16, 'Em andamento'),
            (3, 'MAX12AC', 'MAX 1.2 AC', 'Ana Paula Ribeiro', 'Gustavo Ribeiro', 29, 30, 'Em andamento')
        ]

        dim_projeto_rows = [
            (3, 'PRJ003', 'Unidade Teste Automático', 1, 'João Pedro Alves', 117.09, 3, 5, 'Suspenso'),
            (4, 'PRJ004', 'Conversor DC-DC Isolado', 1, 'Vinícius Moreira', 140.2, 4, 5, 'Em andamento'),
            (9, 'PRJ009', 'Controlador Motor Brushless', 1, 'Patrícia Lima', 95.85, 1, 5, 'Concluído'),
            (16, 'PRJ016', 'Interface SPI ADC', 2, 'Ana Carolina Duarte', 81.82, 17, 18, 'Planejamento'),
            (36, 'PRJ036', 'Conversor USB-Serial', 1, 'Vinícius Moreira', 139.6, 4, 5, 'Planejamento'),
            (42, 'PRJ042', 'Módulo de Telemetria', 1, 'Patrícia Lima', 110.50, 11, 5, 'Em andamento'),
            (55, 'PRJ055', 'Sistema de Resfriamento Líquido', 1, 'Carlos Eduardo', 125.0, 12, 5, 'Concluído'),
            (84, 'PRJ084', 'Conversor USB-Serial 3', 3, 'Lucas Pereira', 128.52, 31, 32, 'Em andamento')
        ]

        dim_tarefa_rows = [
            (1, 'TAR001', 3, 'Levantamento de Requisitos', 'João Pedro Alves', 40, 3, 5, 'Concluído'),
            (2, 'TAR002', 4, 'Desenho de Arquitetura', 'Vinícius Moreira', 80, 4, 5, 'Em andamento'),
            (9, 'TSK009', 3, 'Prototipação da placa', 'Marcelo Cardoso', 46, 4, 5, 'Em andamento'),
            (36, 'TSK036', 36, 'Documentação técnica', 'Tatiane Duarte', 72, 5, 5, 'Não iniciada'),
            (42, 'TSK042', 42, 'Design do circuito RF', 'Patrícia Lima', 120, 11, 5, 'Em andamento'),
            (43, 'TSK043', 42, 'Testes de antena', 'João Pedro Alves', 40, 13, 2, 'Não iniciada'),
            (48, 'TSK048', 16, 'Teste de compatibilidade', 'João Pedro Alves', 113, 19, 20, 'Em andamento'),
            (50, 'TSK050', 84, 'Revisão de BOM', 'Carla Souza', 174, 33, 34, 'Em andamento'),
            (55, 'TSK055', 55, 'Especificação de bombas', 'Carlos Eduardo', 30, 12, 5, 'Concluído'),
            (88, 'TSK088', 16, 'Validação EMC', 'Felipe Rocha', 136, 21, 22, 'Não iniciada')
        ]

        dim_material_rows = [
            (1, 'MAT001', 'Capacitor Cerâmico 10uF 0603', 'Capacitor', 'TDK Corporation', '96.68', 'Ativo'),
            (18, 'MAT018', 'Sensor Corrente ACS712', 'Sensor', 'Infineon Technologies', '14.57', 'Ativo'),
            (20, 'MAT020', 'Sensor Umidade DHT22', 'Sensor', 'Murata', '71.66', 'Obsoleto'),
            (39, 'MAT039', 'Sensor Pressão BMP280', 'Sensor', 'STMicroelectronics', '56.3', 'Ativo'),
            (43, 'MAT043', 'Diodo Retificador UF4007', 'Diodo', 'Texas Instruments', '119.95', 'Ativo'),
            (47, 'MAT047', 'Conector Molex 4 vias', 'Conector', 'NXP Semiconductors', '39.64', 'Ativo'),
            (55, 'MAT055', 'Microcontrolador ARM Cortex-M4', 'Processador', 'STMicroelectronics', '250.00', 'Ativo'),
            (88, 'MAT088', 'Bomba d\'água miniatura 12V', 'Mecânico', 'Bosch', '145.50', 'Ativo'),
            (90, 'MAT090', 'Relé 12V 5A DPDT', 'Relé', 'STMicroelectronics', '108.42', 'Ativo'),
            (92, 'MAT092', 'Antena Patch 2.4GHz', 'Comunicação', 'Taoglas', '80.20', 'Ativo')
        ]

        dim_fornecedor_rows = [
            (1, 'FOR001', 'RTech Distribuidora 1 Ltda', 'Jundiaí', 'SP', 'Materiais de Solda', 'Ativo'),
            (2, 'FOR002', 'Circuitech Distribuidora 2 Ltda', 'Santos', 'SP', 'Componentes Mecânicos', 'Ativo'),
            (3, 'FOR003', 'NovaTech Supply 3 Ltda', 'São Paulo', 'SP', 'Placas de Circuito Impresso', 'Ativo'),
            (4, 'FOR004', 'ElectroTech Global Solutions', 'Campinas', 'SP', 'Componentes Eletrônicos', 'Ativo'),
            (42, 'FOR042', 'ZetaComp Brasil 42 Ltda', 'Campinas', 'SP', 'Materiais de Solda', 'Ativo'),
            (73, 'FOR073', 'Circuitech Distribuidora 73 Ltda', 'Jundiaí', 'SP', 'Materiais de Solda', 'Ativo')
        ]

        dim_solicitacao_rows = [
            (1, 'SC0001', 3, 47, 470, 9, 'Alta', 'Cancelada'),    # 2024-11-03 -> ID 9
            (3, 'SC0003', 9, 43, 286, 7, 'Crítica', 'Rejeitada'),   # 2024-05-18 -> ID 7
            (6, 'SC0006', 84, 90, 201, 38, 'Média', 'Pendente'),    # 2025-02-16 -> ID 38
            (11, 'SC0011', 4, 20, 152, 6, 'Baixa', 'Pendente'),     # 2024-10-15 -> ID 6
            (38, 'SC0038', 3, 1, 280, 8, 'Alta', 'Aprovada'),       # 2024-12-25 -> ID 8
            (42, 'SC0042', 42, 92, 100, 13, 'Média', 'Aprovada'),   # 2025-01-20 -> ID 13
            (55, 'SC0055', 55, 88, 50, 12, 'Baixa', 'Concluída'),   # 2023-08-15 -> Not in DimData! Used ID 12 (10/08/2023) as closest fallback
            (60, 'SC0060', 9, 55, 200, 14, 'Alta', 'Aprovada'),     # 2025-02-02 -> ID 14
            (62, 'SC0062', 16, 18, 232, 23, 'Média', 'Cancelada')   # 2024-07-23 -> ID 23
        ]

        fato_tarefa_rows = [
            (1, 'João Pedro Alves', 20.5, 1, 3),
            (2, 'Vinícius Moreira', 30.0, 2, 4),
            (3, 'Marcelo Cardoso', 5.94, 9, 3),
            (4, 'Tatiane Duarte', 7.86, 36, 10),
            (5, 'Patrícia Lima', 45.0, 42, 11),
            (6, 'Ricardo Teixeira', 7.12, 88, 26),
            (7, 'Patrícia Lima', 10.0, 42, 13),
            (36, 'Carla Souza', 2.17, 50, 35),
            (48, 'Diego Santana', 6.79, 48, 24),
            (86, 'Bruno Oliveira', 8.91, 50, 36),
            (87, 'Bruno Oliveira', 0.92, 48, 25),
            (93, 'Roberto Nogueira', 4.48, 50, 37)
        ]

        fato_empenho_rows = [
            (1, 470, 3, 47, 9),
            (2, 286, 9, 43, 7),
            (3, 152, 4, 20, 6),
            (4, 100, 42, 92, 13),
            (5, 50, 55, 88, 12),
            (6, 200, 9, 55, 14),
            (7, 232, 16, 18, 23),
            (60, 49, 84, 39, 39)
        ]

        fato_compra_rows = [
            (1, 'PED001', 27070.40, 'Concluída', 38, 1, 8, 5),
            (2, 'PED002', 10892.32, 'Pendente', 11, 2, 6, 5),
            (3, 'PED003', 34305.70, 'Cancelada', 3, 3, 7, 5),
            (4, 'PED004', 8020.00, 'Pendente', 42, 4, 13, 5),
            (5, 'PED005', 7275.00, 'Concluída', 55, 2, 12, 5),
            (6, 'PED006', 50000.00, 'Aprovada', 60, 4, 14, 5),
            (7, 'PC0037', 319.73, 'Entregue', 62, 42, 27, 28),
            (84, 'PC0084', 18570.12, 'Aberto', 6, 73, 40, 41)
        ]

        self.stdout.write(self.style.WARNING('Iniciando script de seed com dados mockados hardcoded para o DW...'))

        # Clear existing data using Django ORM
        DimData.objects.all().delete()
        DimPrograma.objects.all().delete()
        DimProjeto.objects.all().delete()
        DimTarefa.objects.all().delete()
        DimMaterial.objects.all().delete()
        DimFornecedor.objects.all().delete()
        DimSolicitacao.objects.all().delete()
        FatoTarefa.objects.all().delete()
        FatoEmpenho.objects.all().delete()
        FatoCompra.objects.all().delete()

        def bulk_insert_with_model(model_class, data, fields):
            """Insert data using Django models instead of raw SQL."""
            if not data:
                return
            objects = []
            for row in data:
                obj_data = {fields[i]: row[i] for i in range(len(fields))}
                objects.append(model_class(**obj_data))
            model_class.objects.bulk_create(objects)

        # Insert data using Django models
        bulk_insert_with_model(DimData, dim_data_rows, ['id', 'dia', 'mes', 'ano'])
        
        bulk_insert_with_model(DimPrograma, dim_programa_rows, 
                              ['id', 'codigo_programa', 'nome_programa', 'gerente_programa', 
                               'gerente_tecnico', 'data_inicio_id', 'data_fim_prevista_id', 'status'])
        
        bulk_insert_with_model(DimProjeto, dim_projeto_rows,
                              ['id', 'codigo_projeto', 'nome_projeto', 'programa_id', 
                               'responsavel', 'custo_hora', 'data_inicio_id', 'data_fim_prevista_id', 'status'])
        
        bulk_insert_with_model(DimTarefa, dim_tarefa_rows,
                              ['id', 'codigo_tarefa', 'projeto_id', 'titulo', 'responsavel', 
                               'estimativa', 'data_inicio_id', 'data_fim_prevista_id', 'status'])
        
        bulk_insert_with_model(DimMaterial, dim_material_rows,
                              ['id', 'codigo_material', 'descricao', 'categoria', 
                               'fabricante', 'custo_estimado', 'status'])
        
        bulk_insert_with_model(DimFornecedor, dim_fornecedor_rows,
                              ['id', 'codigo_fornecedor', 'razao_social', 'cidade', 
                               'estado', 'categoria', 'status'])
        
        bulk_insert_with_model(DimSolicitacao, dim_solicitacao_rows,
                              ['id', 'numero_solicitacao', 'projeto_id', 'material_id', 
                               'quantidade', 'data_solicitacao_id', 'prioridade', 'status'])
        
        bulk_insert_with_model(FatoTarefa, fato_tarefa_rows,
                              ['id', 'usuario', 'horas_trabalhadas', 'tarefa_id', 'data_id'])
        
        bulk_insert_with_model(FatoEmpenho, fato_empenho_rows,
                              ['id', 'quantidade_empenhada', 'projeto_id', 'material_id', 'data_empenho_id'])
        
        bulk_insert_with_model(FatoCompra, fato_compra_rows,
                              ['id', 'numero_pedido', 'valor_total', 'status', 'solicitacao_id', 
                               'fornecedor_id', 'data_pedido_id', 'data_previsao_entrega_id'])

        self.stdout.write(self.style.SUCCESS('Dados DW inseridos com sucesso! Relacionamentos de chaves estritamente mantidos.'))
