import os
import re
from datetime import datetime, date
from django.core.management.base import BaseCommand
from django.db import transaction
import gspread
from google.oauth2 import service_account

# Importe seus modelos do Django aqui
from cadastro.models import (
    InfoInstrumento,
    PontoCalibracao,
    Operadores,
    HistoricoInstrumento,
    TipoInstrumento,
    Marca
)

from inspecao.models import (
    Laboratorio,
    Envio,
    AnaliseCertificado,
)

# --- FUNÇÃO AUXILIAR PARA CONVERTER DATAS ---
def parse_date(date_str):
    """Converte uma string de data para um objeto date, tentando vários formatos."""
    if not date_str or not isinstance(date_str, str):
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            continue
    return None

# --- FUNÇÃO AUXILIAR PARA CONVERTER NÚMEROS ---
def parse_float(num_str):
    """Converte um valor (string ou número) para float, tratando vírgulas e erros."""
    if num_str is None or num_str == '':
        return None
    
    # Se o gspread já retornar um número, o converte para float.
    if isinstance(num_str, (int, float)):
        return float(num_str) / 100
    
    # Se for uma string, que é o esperado, trata a vírgula.
    if isinstance(num_str, str):
        try:
            return float(num_str.replace(',', '.')) / 100
        except (ValueError, TypeError):
            return None
    
    return None

class Command(BaseCommand):
    help = 'Importa dados de calibração de instrumentos de uma planilha do Google Sheets.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando a importação da planilha do Google Sheets...'))

        try:
            # --- CONFIGURAÇÃO E AUTENTICAÇÃO ---
            google_credentials_json = {
                "type": os.environ.get('type'),
                "project_id": os.environ.get('project_id'),
                "private_key_id": os.environ.get('private_key_id'),
                "private_key": os.environ.get('private_key', '').replace('\\n', '\n'),
                "client_email": os.environ.get('client_email'),
                "client_id": os.environ.get('client_id'),
                "auth_uri": os.environ.get('auth_uri'),
                "token_uri": os.environ.get('token_uri'),
                "auth_provider_x509_cert_url": os.environ.get('auth_provider_x509_cert_url'),
                "client_x509_cert_url": os.environ.get('client_x509_cert_url'),
                "universe_domain": os.environ.get('universe_domain'),
            }
            
            scope = [
                'https://www.googleapis.com/auth/spreadsheets',
                "https://www.googleapis.com/auth/drive"
            ]

            credentials = service_account.Credentials.from_service_account_info(
                google_credentials_json, scopes=scope
            )
            gc = gspread.authorize(credentials)

            spreadsheet_key = os.environ.get('PLANO_MESTRE_KEY')
            if not spreadsheet_key:
                self.stdout.write(self.style.ERROR('A variável de ambiente PLANO_MESTRE_KEY não foi definida.'))
                return

            spreadsheet = gc.open_by_key(spreadsheet_key)
            worksheet = spreadsheet.worksheet('BASE PARA SISTEMA DE CALIBRAÇÃO')
            
            # Define os cabeçalhos esperados para evitar o erro de duplicatas
            expected_headers = [
                'TAG', 'EQUIPAMENTO/INSTRUMENTO', 'FAIXA NOMINAL', 'UN', 
                'SETOR ALOCADO', 'RESPONSÁVEL', 'LABORATÓRIO', 'N° DO CERTIFICADO', 
                'DATA ÚLTIMA CALIBRAÇÃO / VERIFICAÇÃO', 'PERIODICIDADE (meses)', 
                'DATA PRÓXIMA CALIBRAÇÃO / VERIFICAÇÃO', 'MÉTODO', 'TENDÊNCIA', 
                'INCERTEZA', 'ERRO TOTAL', 'TOLERÂNCIA ADMISSÍVEL', 
                'ANÁLISE DO CERTIFICADO', 'RESPONSÁVEL ANÁLISE', 'DATA ANÁLISE', 
                'STATUS DO EQUIPAMENTO', 'LINK DO CERTIFICADO'
            ]
            
            # Pega todos os registros da planilha, com cabeçalho na linha 6
            data = worksheet.get_all_records(head=6, expected_headers=expected_headers)
            self.stdout.write(self.style.SUCCESS(f'Foram encontradas {len(data)} linhas de dados na planilha.'))

        except gspread.exceptions.WorksheetNotFound:
            self.stdout.write(self.style.ERROR('A aba "BASE PARA SISTEMA DE CALIBRAÇÃO" não foi encontrada na planilha.'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Falha ao conectar com o Google Sheets: {e}'))
            return

        # --- PROCESSAMENTO DOS DADOS ---
        created_count = 0
        skipped_count = 0
        for index, row in enumerate(data, start=7): # start=7 para corresponder à linha da planilha
            tag = row.get('TAG')

            # Pula a linha se a TAG não estiver preenchida
            if not tag:
                self.stdout.write(self.style.WARNING(f'Linha {index}: TAG não preenchida. Pulando.'))
                skipped_count += 1
                continue
            
            try:
                print(parse_float(row.get('INCERTEZA')))
                print(parse_float(row.get('TENDÊNCIA')))
                # 1. VERIFICA SE O INSTRUMENTO EXISTE
                try:
                    instrumento = InfoInstrumento.objects.get(tag=tag)
                except InfoInstrumento.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Linha {index} (TAG: {tag}): Instrumento não encontrado. Criando novo instrumento...'))
                    
                    # Cria o instrumento com valores padrão (você pode ajustar conforme necessário)
                    instrumento = InfoInstrumento(
                        tag=tag,
                        tipo_instrumento=TipoInstrumento.objects.get_or_create(
                            nome=row.get('EQUIPAMENTO/INSTRUMENTO', 'Desconhecido')
                        )[0],
                        marca=Marca.objects.get_or_create(
                            nome='N/A'
                        )[0],
                        status_instrumento='ativo',
                        tempo_calibracao=365,  # Valor padrão de 1 ano
                        ultima_calibracao=date.today()
                    )
                    instrumento.save()
                    
                    self.stdout.write(self.style.SUCCESS(f'Instrumento {tag} criado com sucesso.'))

                # 2. VERIFICA SE JÁ EXISTE UM ENVIO PARA ESTA DATA
                data_calibracao = parse_date(row.get('DATA ÚLTIMA CALIBRAÇÃO / VERIFICAÇÃO'))
                if not data_calibracao:
                    self.stdout.write(self.style.WARNING(f'Linha {index} (TAG: {tag}): Data de calibração inválida ou vazia. Pulando.'))
                    skipped_count += 1
                    continue

                if Envio.objects.filter(instrumento=instrumento, data_retorno=data_calibracao).exists():
                    self.stdout.write(self.style.NOTICE(f'Linha {index} (TAG: {tag}): Já existe um envio/calibração para esta data. Pulando.'))
                    skipped_count += 1
                    continue
                
                # Inicia uma transação para garantir a integridade dos dados
                with transaction.atomic():
                    # --- CRIAÇÃO/OBTENÇÃO DE OBJETOS RELACIONADOS ---

                    # Ponto de Calibração: Apenas busca, não cria.
                    try:
                        ponto_calibracao = PontoCalibracao.objects.get(
                            instrumento=instrumento,
                            descricao=row.get('EQUIPAMENTO/INSTRUMENTO', 'N/A'),
                            faixa_nominal=row.get('FAIXA NOMINAL', 'N/A'),
                        )
                    except PontoCalibracao.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Linha {index} (TAG: {tag}): Ponto de calibração não encontrado. Criando novo ponto..."))
                        
                        ponto_calibracao = PontoCalibracao(
                            descricao=row.get('EQUIPAMENTO/INSTRUMENTO', 'N/A'),
                            instrumento=instrumento,
                            faixa_nominal=row.get('FAIXA NOMINAL', 'N/A'),
                            unidade=row.get('UN', '-'),
                            tolerancia_admissivel=parse_float(row.get('TOLERÂNCIA ADMISSÍVEL')),
                            status_ponto_calibracao='ativo'
                        )
                        ponto_calibracao.save()
                        self.stdout.write(self.style.SUCCESS(f'Ponto de calibração criado com sucesso.'))
                    
                    # Laboratório
                    nome_laboratorio = row.get('LABORATÓRIO')
                    if not nome_laboratorio:
                         self.stdout.write(self.style.WARNING(f'Linha {index} (TAG: {tag}): Nome do laboratório não preenchido. Pulando.'))
                         skipped_count +=1
                         continue # Pula para a próxima iteração do loop

                    laboratorio, _ = Laboratorio.objects.get_or_create(
                        nome=nome_laboratorio,
                        defaults={'status': 'ativo'}
                    )

                    dict_responsavel = {
                        'Matheus': 4397,
                        'Severiano': 4358 
                    }
                    
                    # Responsável Análise (Operador)
                    responsavel_analise_obj = None
                    nome_responsavel_analise = row.get('RESPONSÁVEL ANÁLISE')
                    if nome_responsavel_analise:
                        responsavel_analise_obj = Operadores.objects.get(
                            matricula=dict_responsavel[nome_responsavel_analise],
                        )

                    # --- CRIAÇÃO DO ENVIO E DA ANÁLISE ---

                    # Mapeia o método
                    metodo_map = {'Interno': 'interno', 'Externo': 'externo'}
                    metodo = metodo_map.get(row.get('MÉTODO'), 'externo') # Default para externo

                    # Cria o Envio
                    novo_envio = Envio.objects.create(
                        instrumento=instrumento,
                        ponto_calibracao=ponto_calibracao,
                        data_envio=data_calibracao,
                        data_retorno=data_calibracao,
                        laboratorio=laboratorio,
                        natureza='calibracao', # Default
                        status='recebido', # Já que estamos analisando o certificado
                        pdf=row.get('LINK DO CERTIFICADO'),
                        metodo=metodo,
                        analise=True, # Marcamos como analisado
                        observacoes=f"Importado via planilha. Certificado: {row.get('N° DO CERTIFICADO')}"
                    )
                    
                    # Mapeia a análise
                    analise_map = {'Aprovado': 'aprovado', 'Reprovado': 'reprovado'}
                    analise_status = analise_map.get(row.get('ANÁLISE DO CERTIFICADO'))

                    # Cria a Análise do Certificado
                    AnaliseCertificado.objects.create(
                        envio=novo_envio,
                        analise_certificado=analise_status,
                        incerteza=parse_float(row.get('INCERTEZA')),
                        tendencia=parse_float(row.get('TENDÊNCIA')),
                        responsavel_analise=responsavel_analise_obj,
                        data_analise=parse_date(row.get('DATA ANÁLISE'))
                    )

                    # --- CRIAÇÃO DO REGISTRO NO HISTÓRICO ---
                    tipos_historico = {
                        'enviado': f"Registro de envio para calibração no laboratório {row.get('LABORATÓRIO', 'N/A')}, importado via planilha.",
                        'recebido': f'Instrumento no ponto {novo_envio.ponto_calibracao}, recebido do laboratório {novo_envio.laboratorio} dia {data_calibracao}. <a href="{row.get("LINK DO CERTIFICADO")}" target="_blank">Link do Certificado</a>',
                        'analisado': (
                            f"Análise do certificado {row.get('N° DO CERTIFICADO', 'N/A')} realizada. "
                            f"Resultado: {row.get('ANÁLISE DO CERTIFICADO', 'N/A')}. Importado via planilha."
                        )
                    }

                    for tipo, descricao in tipos_historico.items():
                        HistoricoInstrumento.objects.create(
                            instrumento=instrumento,
                            ponto_calibracao=ponto_calibracao,
                            tipo_mudanca=tipo,
                            descricao_mudanca=descricao
                        )

                    # --- ATUALIZAÇÃO DO INSTRUMENTO ---
                    periodicidade_meses = row.get('PERIODICIDADE (meses)')
                    if periodicidade_meses and isinstance(periodicidade_meses, int) and periodicidade_meses > 0:
                        instrumento.tempo_calibracao = periodicidade_meses * 30 # Converte meses para dias
                    
                    instrumento.ultima_calibracao = data_calibracao
                    
                    # O método save() do InfoInstrumento irá recalcular a próxima calibração
                    instrumento.save() 
                    
                    self.stdout.write(self.style.SUCCESS(f'Linha {index} (TAG: {tag}): Envio e análise importados com sucesso!'))
                    created_count += 1

            except Operadores.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Linha {index} (TAG: {tag}): Operador não encontrado no banco de dados. Pulando.'))
                skipped_count += 1
                continue
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Linha {index} (TAG: {tag}): Ocorreu um erro inesperado: {e}'))
                skipped_count += 1
                # Se ocorrer um erro, a transação garante que nada foi salvo
                continue

        self.stdout.write(self.style.SUCCESS('\n--- Resumo da Importação ---'))
        self.stdout.write(self.style.SUCCESS(f'Registros criados: {created_count}'))
        self.stdout.write(self.style.WARNING(f'Linhas puladas/ignoradas: {skipped_count}'))
        self.stdout.write(self.style.SUCCESS('Importação finalizada.'))

