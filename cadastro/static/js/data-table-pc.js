$(document).ready(function () {
    const table = $('#instrumentos-table').DataTable({
        processing: true,
        serverSide: true,
        ajax: {
            url: '/instrumentos-data/', // URL da view criada
            type: 'GET',
            data: function (d) {
                // Adiciona os filtros personalizados, se necessário
                // Exemplo:
                // d.status = $('#filterStatus').val();
                // d.area = $('#filterArea').val();
                // d.solicitante = $('#filterSolicitante').val();
                // d.data_inicio = $('#filterDataInicio').val();
            }
        },
        columns: [
            {
                className: 'details-control',
                orderable: false,
                data: null,
                defaultContent: '<i class="fa fa-plus-circle text-primary" title="Expandir"></i>',
            },
            { data: 'tag', title: 'Tag' },
            { data: 'tipo_instrumento', title: 'Tipo de Instrumento' },
            { data: 'marca', title: 'Marca' },
            { 
                data: 'status_instrumento',
                title: 'Status',
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
                render: function (data) {
                    if (data.includes('Atrasado')) {
                        return `<span class="text-danger">${data}</span>`;
                    }
                    return data;
                },
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
            {
                data: null, 
                orderable: false, 
                render: function(data, type, row) {

                    const ultimoEnvioList = row.pontos_calibracao.map(ponto => ponto.ultimo_envio_pk);
                    const analise_certificados = row.pontos_calibracao.map(ponto => ponto.analise_certificado);
                    const contem_null = analise_certificados.some(certificado => certificado === null);
                    const todos_certificados_true = analise_certificados.every(certificado => certificado === true);

                    let buttons = `
                        <button class="btn badge btn-primary btn-sm" onclick="abrirQrCodeModal('${row.tag}')">Ver QR Code</button>
                        <button class="btn badge btn-secondary btn-sm" onclick="abrirHistoricoModal('${row.tag}','${row.ponto_pk}')">Histórico</button>
                    `; 

                    console.log(row)

                    if (row.status_calibracao === 'enviado') {
                        buttons += `<button class="btn badge btn-success btn-sm" onclick="receberCalibracao('${JSON.stringify(ultimoEnvioList)}','${row.tag}')">Receber</button>`;
                    } else if (row.status_calibracao === 'recebido' && contem_null) {
                        buttons += ``;
                    } else if (row.status_calibracao === 'recebido' && todos_certificados_true) {
                        buttons += `<button class="btn badge btn-warning btn-sm" onclick="enviarCalibracao('${row.tag}','${row.ponto_pk}')">Enviar</button>`;
                    } else {
                        buttons += `<button class="btn badge btn-warning btn-sm" onclick="enviarCalibracao('${row.tag}','${row.ponto_pk}')">Enviar</button>`;
                    }
                    return buttons;
                }
            },
        ],
        order: [[1, 'asc']],
    });

    $('#instrumentos-table tbody').on('click', 'td.details-control', function () {
        const tr = $(this).closest('tr');
        const row = table.row(tr);

        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');
        } else {
            row.child(format(row.data())).show();
            tr.addClass('shown');
        }
    });

    function format(d) {
        return `
            <table cellpadding="5" cellspacing="0" border="0" style="padding-left:50px;">
                ${d.pontos_calibracao
                    .map(
                        (p) => `
                        <tr>
                            <td>Descrição:</td><td>${p.ponto_descricao}</td>
                            <td>Faixa Nominal:</td><td>${p.ponto_faixa_nominal}</td>
                            <td>Unidade:</td><td>${p.ponto_unidade}</td>
                            <td>Tolerância Admissível:</td><td>${p.ponto_tolerancia_admissivel}</td>
                            
                            <!-- Último Certificado -->
                            <td>Último Certificado:</td>
                            <td>
                                ${p.ultimo_certificado === 'reprovado' ? 
                                    '<span class="badge bg-danger">Reprovado</span>' :
                                    p.ultimo_certificado === 'aprovado' ? 
                                        '<span class="badge bg-success">Aprovado</span>' :
                                        '<span class="badge bg-warning">Pendente</span>'
                                }
                            </td>
                            <td>
                                 ${d.status_calibracao === 'recebido' && p.analise_certificado === null && p.status_ponto_calibracao == 'ativo' ? 
                                    `Calibração: <button class="btn badge btn-danger btn-sm" onclick="analisarCalibracao('${p.ultimo_envio_pk}','${d.tag}','${p.ponto_pk}')">Analisar</button>` :
                                    ``
                                }
                            </td>
                            <td><button class="btn badge btn-secondary btn-sm" onclick="abrirHistoricoModal('${d.tag}','${p.ponto_pk}','${p.ponto_descricao}')">Histórico</button></td>
                            <td>
                                Status:
                                 ${p.status_ponto_calibracao == 'ativo' ? 
                                    ' <span class="badge bg-success">Ativo</span>' :
                                    ' <span class="badge bg-danger">Inativo</span>'
                                }
                            </td>
                        </tr>
                    `
                    )
                    .join('')}
            </table>
        `;
    }
    
});