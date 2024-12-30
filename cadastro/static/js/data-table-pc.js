$(document).ready(function () {
    const table = $('#instrumentos-table').DataTable({
        processing: true,
        serverSide: true,
        ajax: {
            url: '/instrumentos-data/', // URL da view criada
            type: 'GET',
            data: function (d) {
                // Adiciona os filtros personalizados, se necessário
                // d.status = $('#filterStatus').val();
                // d.area = $('#filterArea').val();
                // d.solicitante = $('#filterSolicitante').val();
                // d.data_inicio = $('#filterDataInicio').val();
            }
        },
        columns: [
            { data: 'tag', title: 'Tag do Instrumento', orderable: true },
            { data: 'tipo_instrumento', title: 'Tipo de Instrumento' },
            { data: 'marca', title: 'Marca' },
            { 
                data: 'status_instrumento',
                orderable: true, 
                render: function(data, type, row) {
                    if (row.status_instrumento === 'ativo') {
                        return `<span class="badge bg-success">Ativo</span>`;
                    } else if (row.status_instrumento === 'inativo') {
                        return `<span class="badge bg-secondary">Inativo</span>`;
                    } else if (row.status_instrumento === 'em_uso') {
                        return `<span class="badge bg-primary">Em Uso</span>`;
                    } else if (row.status_instrumento === 'desuso') {
                        return `<span class="badge bg-warning">Desuso</span>`;
                    } else if (row.status_instrumento === 'danificado') {
                        return `<span class="badge bg-danger">Danificado</span>`;
                    } else {
                        return `<span class="badge bg-dark">Desconhecido</span>`;
                    }
                }
            },
            { data: 'ultima_calibracao', title: 'Última Calibração' },
            { data: 'proxima_calibracao', title: 'Próxima Calibração' },
            { 
                data: 'status_calibracao_string',
                title: 'Status da Calibração',
                render: function(data, type, row) {
                    if (row.status_calibracao_string.includes("Atrasado")) {
                        // Adiciona o ícone de atenção ao lado do texto
                        return `
                            ${row.status_calibracao_string} 
                            <i class="fa fa-exclamation-circle text-danger" aria-hidden="true" title="Calibração atrasada"></i>
                        `;
                    } else {
                        return `${row.status_calibracao_string}`;
                    }
                }
            },
            {   
                data: 'responsavel',
                orderable: true,
                render: function(data, type, row) {
                    if (row.responsavel === null) {
                        return `<button class="btn badge btn-secondary btn-sm" onclick="abrirModalEscolherResponsavel('${row.tag}')">Escolher responsável</button>`;
                    } else {
                        return `<span class="badge bg-primary">${row.responsavel}</span>`;
                    }
                }
            },
            { data: 'ponto_descricao', title: 'Descrição do Ponto' },
            { data: 'ponto_faixa_nominal', title: 'Faixa Nominal' },
            { data: 'ponto_unidade', title: 'Unidade' },
            { data: 'ponto_tolerancia_admissivel', title: 'Tolerância Admissível' },
            {
                data: 'ultimo_certificado', // Define o campo de origem para a ordenação
                orderable: true,
                render: function(data, type, row) {
                    if (type === 'display') {
                        // Renderiza o conteúdo visual para exibição
                        if (data === 'reprovado') {
                            return `<span class="badge bg-danger">Reprovado</span>`;
                        } else if (data === 'aprovado') {
                            return `<span class="badge bg-success">Aprovado</span>`;
                        } else {
                            return `<span class="badge bg-warning">Pendente</span>`;
                        }
                    }
                    // Retorna o valor bruto para ordenação e pesquisa
                    return data;
                }
            },
            {
                data: null, 
                orderable: false, 
                render: function(data, type, row) {
                    
                    let buttons = `
                        <button class="btn badge btn-primary btn-sm" onclick="abrirQrCodeModal('${row.tag}')">Ver QR Code</button>
                        <button class="btn badge btn-secondary btn-sm" onclick="abrirHistoricoModal('${row.tag}','${row.ponto_pk}')">Histórico</button>
                    `;

                    if (row.status_calibracao === 'enviado') {
                        buttons += `<button class="btn badge btn-success btn-sm" onclick="receberCalibracao('${row.ultimo_envio_pk}','${row.tag}')">Receber</button>`;
                    } else if (row.status_calibracao === 'recebido' && row.analise_certificado === null) {
                        buttons += `<button class="btn badge btn-danger btn-sm" onclick="analisarCalibracao('${row.ultimo_envio_pk}','${row.tag}','${row.ponto_pk}')">Analisar</button>`;
                    } else if (row.status_calibracao === 'recebido' && row.analise_certificado === true) {
                        buttons += `<button class="btn badge btn-warning btn-sm" onclick="enviarCalibracao('${row.tag}','${row.ponto_pk}')">Enviar</button>`;
                    } else {
                        buttons += `<button class="btn badge btn-warning btn-sm" onclick="enviarCalibracao('${row.tag}','${row.ponto_pk}')">Enviar</button>`;
                    }

                    return buttons;
                }
            }
        ],
        order: [[1, 'asc']],
        language: {
            lengthMenu: "Exibir _MENU_ registros por página",
            zeroRecords: "Nenhuma execução encontrada",
            info: "Exibindo _START_ a _END_ de _TOTAL_ registros",
            infoEmpty: "Nenhum registro disponível",
            infoFiltered: "(filtrado de _MAX_ registros no total)"
        }
    });
});