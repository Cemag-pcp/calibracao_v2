from django.shortcuts import render
from openpyxl import load_workbook
import os
import copy
from django.http import JsonResponse, HttpResponse
from cadastro.models import Funcionario, PontoCalibracao
from ficha.models import AssinaturaInstrumento

# Create your views here.

def ficha_por_funcionario(request):

    if request.method == 'GET':

        funcionarios = Funcionario.objects.all()

        return render(request, "ficha.html",{"funcionarios":funcionarios})

def emissao_ficha_por_funcionario(request, id):
    if request.method == 'GET':
        funcionario = Funcionario.objects.filter(pk=id).first()

        if funcionario:
            # Converte o QuerySet em uma lista de dicionários
            assinatura_funcionario = AssinaturaInstrumento.objects.filter(assinante=funcionario)

            wb = load_workbook("Termo de Responsabilidade Equipamentos de Medição.xlsx")

            ws = wb.active
            if assinatura_funcionario:
                for i, assinatura in enumerate(assinatura_funcionario):
                    linha_destino = 18 + i

                    # Copia o valor e o estilo da linha 18 para a linha de destino
                    for coluna in range(1, 11):  # A coluna 1 é a A, a coluna 2 é a B, etc.
                        ws.cell(row=linha_destino, column=coluna).font = copy.copy(ws.cell(row=18, column=coluna).font)
                        ws.cell(row=linha_destino, column=coluna).fill = copy.copy(ws.cell(row=18, column=coluna).fill)
                        ws.cell(row=linha_destino, column=coluna).border = copy.copy(ws.cell(row=18, column=coluna).border)
                        ws.cell(row=linha_destino, column=coluna).alignment = copy.copy(ws.cell(row=18, column=coluna).alignment)
                                # Access and copy the line height from row 27
                    line_height = ws.row_dimensions[18].height  # Access height from source row
                    ws.row_dimensions[linha_destino].height = line_height  # Set the same height for the target row

                    pontos_calibracao = assinatura.instrumento.pontos_calibracao.filter(status_ponto_calibracao='ativo')
                    ponto_calibracao_str = ", ".join([ponto.faixa_nominal for ponto in pontos_calibracao])
                    ws.cell(row=linha_destino, column=1, value=assinatura.data_entrega.strftime("%d/%m/%Y"))
                    ws.cell(row=linha_destino, column=2, value=assinatura.instrumento.tipo_instrumento.nome)
                    ws.cell(row=linha_destino, column=5, value=assinatura.instrumento.tag)
                    ws.cell(row=linha_destino, column=7, value=ponto_calibracao_str)
                    ws.cell(row=linha_destino, column=8, value=assinatura.motivo)

                    
                    ws.merge_cells(start_row=linha_destino, start_column=2, end_row=linha_destino, end_column=4)
                    ws.merge_cells(start_row=linha_destino, start_column=5, end_row=linha_destino, end_column=6)
                    ws.merge_cells(start_row=linha_destino, start_column=10, end_row=linha_destino, end_column=11)
            
            ws['B6'] = funcionario.nome
            ws['H6'] = funcionario.matricula
            ws['H7'] = funcionario.setor.nome
            
            # Criar a pasta 'ficha' se não existir
            output_dir = "media/ficha"

            # Salvar o workbook modificado dentro da pasta 'ficha'
            output_file_path = os.path.join(output_dir, f"Termo de Responsabilidade Equipamentos de Medição_Atualizado-{funcionario.nome}.xlsx")
            wb.save(output_file_path)

            wb.close()

            # Preparar o arquivo para download
            with open(output_file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = f'attachment; filename="Termo de Responsabilidade Equipamentos de Medição_Atualizado-{funcionario.nome}.xlsx"'

            return response
        else:
            return JsonResponse({"message": "Funcionário não encontrado"}, status=404)