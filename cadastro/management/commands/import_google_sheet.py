# app/management/commands/import_google_sheet.py
import os
from django.core.management.base import BaseCommand
import gspread
from google.oauth2 import service_account
from collections import defaultdict
from datetime import datetime
from ...models import Marca, Unidade, TipoInstrumento, PontoCalibracao, InfoInstrumento
from django.utils.dateparse import parse_date

def parse_float(value):
    if not value:
        return None
    try:
        # Substitui vírgula por ponto e remove espaços
        return float(value.replace(',', '.').strip())
    except ValueError:
        return None

def encontrar_tipo_instrumento_similar(nome, tipos_existentes):
    """
    Encontra um tipo de instrumento existente que seja similar ao nome fornecido.
    Retorna o objeto encontrado ou None se não encontrar.
    """
    nome = nome.lower().strip()
    
    # Primeiro verifica se existe exatamente (case insensitive)
    for tipo in tipos_existentes:
        if tipo.nome.lower() == nome:
            return tipo
    
    # Remove sufixos comuns entre parênteses
    nome_base = nome.split('(')[0].strip()
    
    # Verifica se o nome base existe
    for tipo in tipos_existentes:
        if tipo.nome.lower().split('(')[0].strip() == nome_base:
            return tipo
    
    # Verifica se o nome base está contido em algum tipo existente ou vice-versa
    for tipo in tipos_existentes:
        tipo_nome = tipo.nome.lower()
        if nome_base in tipo_nome or tipo_nome in nome_base:
            return tipo
    
    return None


class Command(BaseCommand):
    help = 'Importa dados específicos de instrumentos de uma planilha do Google Sheets'

    def handle(self, *args, **options):
        # Configura as credenciais
        google_credentials_json = {
            "type": os.environ.get('type'),
            "project_id": os.environ.get('project_id'),
            "private_key": os.environ.get('private_key'),
            "private_key_id": os.environ.get('private_key_id'),
            "client_x509_cert_url": os.environ.get('client_x509_cert_url'),
            "client_email": os.environ.get('client_email'),
            "auth_uri": os.environ.get('auth_uri'),
            "auth_provider_x509_cert_url": os.environ.get('auth_provider_x509_cert_url'),
            "universe_domain": os.environ.get('universe_domain'),
            "client_id": os.environ.get('client_id'),
            "token_uri": os.environ.get('token_uri'),
        }

        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive"
        ]

        # Ajusta a chave privada
        google_credentials_json["private_key"] = google_credentials_json["private_key"].replace("\\n", "\n")

        try:
            # Autentica
            credentials = service_account.Credentials.from_service_account_info(
                google_credentials_json, scopes=scope
            )
            gc = gspread.authorize(credentials)

            # Abre a planilha
            spreadsheet_key = os.environ.get('PLANO_MESTRE_KEY')
            spreadsheet = gc.open_by_key(spreadsheet_key)

            # Lê a primeira worksheet
            worksheet = spreadsheet.worksheets()[4]
            
            # Define o mapeamento das colunas (A=1, B=2, C=3, D=4, I=9, P=16)
            COL_MAP = {
                'tag': 1,            # Coluna A
                'equipamento': 2,    # Coluna B
                'faixa_nominal': 3,  # Coluna C
                'unidade': 4,        # Coluna D
                'data_calibracao': 9,# Coluna I
                'tolerancia': 16     # Coluna P
            }
            
            # Obtém o cabeçalho da linha 6 para validação
            header_row = 6
            headers = [worksheet.cell(header_row, col).value.strip() for col in COL_MAP.values()]
            
            # Validação dos cabeçalhos esperados
            expected_headers = ['TAG', 'EQUIPAMENTO/INSTRUMENTO', 'FAIXA NOMINAL', 
                            'UN', 'DATA ÚLTIMA CALIBRAÇÃO / VERIFICAÇÃO', 'TOLERÂNCIA ADMISSÍVEL']
            
            for i, (expected, actual) in enumerate(zip(expected_headers, headers)):
                if expected != actual:
                    self.stdout.write(self.style.ERROR(
                        f"Cabeçalho inválido na coluna {list(COL_MAP.keys())[i]}. "
                        f"Esperado: '{expected}', Encontrado: '{actual}'"
                    ))
                    return

            # Obtém ou cria a marca padrão "N/A"
            marca_na, _ = Marca.objects.get_or_create(nome="N/A")
            
            # Processa os dados a partir da linha 7
            data_start_row = 7
            created_count = 0
            updated_count = 0
            skipped_count = 0
            
            # Pega todas as linhas a partir da linha 7
            all_rows = worksheet.get_all_values()[data_start_row-1:]  # -1 porque é baseado em 0
            
            # Pré-carrega todos os tipos de instrumento existentes
            tipos_existentes = list(TipoInstrumento.objects.all())
            # Pré-carrega todas as unidades existentes
            unidades_existentes = list(Unidade.objects.all())

            for row_idx, row in enumerate(all_rows, start=data_start_row):
                if not any(row):  # Ignora linhas vazias
                    skipped_count += 1
                    continue
                
                try:
                    # Extrai os valores das colunas mapeadas
                    values = {
                        key: row[col-1] if col-1 < len(row) else None 
                        for key, col in COL_MAP.items()
                    }
                    
                    # Pula linhas sem TAG
                    if not values['tag'] or not values['tag'].strip():
                        skipped_count += 1
                        continue
                        
                    # Processa a data de calibração
                    try:
                        data_str = values['data_calibracao'].strip()
                        if data_str:
                            # Tenta parse no formato brasileiro DD/MM/YYYY
                            day, month, year = map(int, data_str.split('/'))
                            data_calibracao = datetime(year, month, day).date()
                        else:
                            raise ValueError("Data vazia")
                    except (ValueError, TypeError):
                        self.stdout.write(self.style.WARNING(
                            f"Linha {row_idx}: Data de calibração inválida '{values['data_calibracao']}'. "
                            f"Usando data atual."
                        ))
                        data_calibracao = datetime.now().date()
                    
                    # Verifica/obtém o Tipo de Instrumento com tratamento especial
                    tipo_nome = values['equipamento'].strip() if values['equipamento'] else "Desconhecido"
                    
                    # Primeiro tenta encontrar um tipo similar
                    tipo_existente = encontrar_tipo_instrumento_similar(tipo_nome, tipos_existentes)
                    
                    if tipo_existente:
                        tipo_instrumento = tipo_existente
                        tipo_created = False
                        self.stdout.write(self.style.WARNING(
                            f"Usando tipo existente '{tipo_existente.nome}' para '{tipo_nome}'"
                        ))
                    else:
                        tipo_instrumento, tipo_created = TipoInstrumento.objects.get_or_create(
                            nome=tipo_nome
                        )
                        if tipo_created:
                            tipos_existentes.append(tipo_instrumento)  # Adiciona à lista para futuras verificações
                            self.stdout.write(self.style.SUCCESS(
                                f"Criado novo TipoInstrumento: {tipo_nome}"
                            ))
                    
                    # Verifica/obtém a Unidade
                    unidade_nome = values['unidade'].strip() if values['unidade'] else "-"

                    unidade_obj, unidade_created = Unidade.objects.get_or_create(
                        nome=unidade_nome
                    )
                    if unidade_created:
                        unidades_existentes.append(unidade_obj)
                        self.stdout.write(self.style.SUCCESS(
                            f"Criada nova Unidade: {unidade_nome}"
                        ))
                    
                    # Verifica se a TAG já existe
                    try:
                        instrumento = InfoInstrumento.objects.get(tag=values['tag'])
                        updated_count += 1
                        action = "Atualizado"
                        marca = instrumento.marca
                    except InfoInstrumento.DoesNotExist:
                        instrumento = InfoInstrumento(tag=values['tag'])
                        created_count += 1
                        action = "Criado"
                        marca = marca_na
                        instrumento.ultima_calibracao = data_calibracao
                    
                    # Atualiza os campos do instrumento
                    instrumento.tipo_instrumento = tipo_instrumento
                    instrumento.marca = marca
                    instrumento.tempo_calibracao = 365  # Valor padrão, pode ser ajustado
                    instrumento.save()
                    
                    # Processa o ponto de calibração
                    ponto, ponto_created = PontoCalibracao.objects.get_or_create(
                        instrumento=instrumento,
                        defaults={
                            'descricao': tipo_nome,
                            'unidade': unidade_nome,
                            'faixa_nominal': values['faixa_nominal'] or "N/A",
                            'tolerancia_admissivel': parse_float(values['tolerancia']),
                        }
                    )

                    # E também atualize a parte de atualização do ponto existente:
                    if not ponto_created:
                        ponto.descricao = tipo_nome
                        ponto.unidade = unidade_nome
                        ponto.faixa_nominal = values['faixa_nominal'] or "N/A"
                        ponto.tolerancia_admissivel = parse_float(values['tolerancia'])
                        ponto.save()
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"{action} instrumento {values['tag']} - {tipo_nome}"
                    ))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Erro ao processar linha {row_idx}: {str(e)}"
                    ))
                    skipped_count += 1
            
            # Resumo final
            self.stdout.write("\n" + "="*50)
            self.stdout.write(self.style.SUCCESS("Importação concluída!"))
            self.stdout.write(f"Total de linhas processadas: {len(all_rows)}")
            self.stdout.write(f"Novos instrumentos criados: {created_count}")
            self.stdout.write(f"Instrumentos atualizados: {updated_count}")
            self.stdout.write(f"Linhas ignoradas: {skipped_count}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao acessar a planilha: {str(e)}"))