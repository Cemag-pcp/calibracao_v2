$(document).ready(function () {
    const table = $('#instrumentos-table').DataTable({
        processing: true,
        serverSide: true,
        pageLength: 10, // Itens por página
        lengthMenu: [[10, 25, 50], [10, 25, 50]], // Opções de paginação
        ajax: {
            url: '/instrumentos-data/', // URL da view criada
            type: 'GET',
            data: function (d) {
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
            { data: 'tipo_instrumento', title: 'Tipo de Instrumento'},
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
            { data: 'proxima_calibracao', title: 'Próxima Calibração', orderable: false },
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
                data: 'status_calibracao_string',
                title: 'Status Geral',
                render: function (data, type, row) {
                    const ultimoEnvioList = row.pontos_calibracao.map(ponto => ponto.ultimo_certificado);
                    const contemAprovado = ultimoEnvioList.some(aprovado => aprovado === "aprovado" || aprovado === null);

                    const aprovado = contemAprovado ? '<i class="fa-solid fa-circle fa-circle-check"  style="color:rgb(0, 124, 37);"></i>' : '<i class="fa-solid fa-circle-xmark" style="color: #ff0000;"></i>'

                    return aprovado;
                },
            },
            {   
                data: 'responsavel',
                orderable: true,
                render: function(data, type, row) {
                    if (row.status_calibracao === 'enviado') {
                        return ``
                    } else if (row.responsavel.matriculaNome === null) {
                        return `<button class="btn badge btn-secondary btn-sm" onclick="abrirModalEscolherResponsavel('${row.tag}')">Escolher responsável</button>`;
                    } else {
                        return `<span class="btn badge btn-primary" onclick="visualizarResponsavel('${row.tag}','${row.responsavel.id}','${row.responsavel.dataEntrega}')">${row.responsavel.matriculaNome}</span>`;
                    }
                }
            },
            {
                data: null, 
                orderable: false, 
                render: function(data, type, row) {

                    const ultimoEnvioList = row.pontos_calibracao.map(ponto => ponto.ultimo_envio_pk);

                    // Filtra os pontos onde ultimo_envio_pk não é null e mapeia os analise_certificado
                    const analise_certificados = row.pontos_calibracao
                        .filter(ponto => ponto.ultimo_envio_pk !== null)
                        .map(ponto => ponto.analise_certificado);
                    
                    // Verifica se há algum certificado null na lista filtrada
                    const contem_null = analise_certificados.some(certificado => certificado === null);
                    
                    // Verifica se todos os certificados na lista filtrada são true
                    const todos_certificados_true = analise_certificados.every(certificado => certificado === true);

                    let buttons = `
                        <td data-title="Exec">
                            <div class="col-sm-4 d-flex dropdown justify-content-center align-items-center"
                                style="padding-left: 0.35rem;">
                                <a data-bs-toggle="dropdown" aria-expanded="false"
                                    style="cursor: pointer;">
                                    <i class="fa-solid fa-angle-down" style="color:black;"></i>
                                </a>
                                <ul class="dropdown-menu">
                                    <li><p class="dropdown-header">Histórico</p></li>
                                    <li><a class="dropdown-item" style="cursor:pointer" onclick="abrirQrCodeModal('${row.tag}')">
                                        Ver QR Code
                                    </a></li>
                    `; 


                    if (row.status_calibracao !== 'enviado' && row.status_instrumento !== 'danificado') {
                        buttons +=`<li>
                                        <hr class="dropdown-divider">
                                    </li>
                                    <li>
                                        <p class="dropdown-header">Item</p>
                                    </li>`
                        if(row.responsavel.id !== null) {
                            buttons += `<li>
                                            <a class="dropdown-item" style="cursor:pointer" responsavel-id="${row.responsavel.id}"  onclick="alterarResponsavel('${row.tag}','${row.responsavel.id}')">
                                                Alterar Responsável
                                            </a>
                                        </li>`;
                        }    
                        buttons += `<li>
                            <a class="dropdown-item" style="cursor:pointer"  onclick="substituicaoInstrumento('${row.tag}','${row.responsavel.id}','${row.id}')">
                                Danificado
                            </a>
                        </li>`;
                    }

                    if (row.status_calibracao === 'enviado') {
                        buttons += `<li><hr class="dropdown-divider"></li>
                                    <li><p class="dropdown-header">Status: A Receber</p></li>
                                    <li><a class="dropdown-item" style="cursor:pointer" onclick="receberCalibracao('${JSON.stringify(ultimoEnvioList)}', '${row.tag}', '${row.ultimo_assinante.nome}')">
                                        Receber
                                    </a></li>`;
                    } else if (row.status_calibracao === 'recebido' && contem_null) {
                        buttons += `<li><hr class="dropdown-divider"></li>
                                    <li><p class="dropdown-header">Status: A Analisar</p></li>`;
                    } else if (row.status_calibracao === 'recebido' && todos_certificados_true) {
                        buttons += `<li><hr class="dropdown-divider"></li>
                                    <li><p class="dropdown-header">Status: A Enviar</p></li>
                                    <li><a class="dropdown-item" style="cursor:pointer"  onclick="enviarCalibracao('${row.tag}','${row.ponto_pk}','${row.responsavel.matriculaNome}')">
                                        Enviar
                                    </a></li>`;
                    } else {
                        buttons += `<li><hr class="dropdown-divider"></li>
                                    <li><p class="dropdown-header">Status: A Enviar</p></li>
                                    <li><a class="dropdown-item" style="cursor:pointer"  onclick="enviarCalibracao('${row.tag}','${row.ponto_pk}','${row.responsavel.matriculaNome}')">
                                        Enviar
                                    </a></li>`;
                    }
                    
                    buttons += `</ul>
                            </div>
                        </td>`
                    return buttons;
                }
            },
        ],
        responsive: true,
        autoWidth: false,       // Desativa ajuste automático da largura das colunas
        searching: false,
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
            console.log(row.data())
        }
    });

    function format(d) {
        return `
            <div class="card-container">
                <div class="row">
                ${d.pontos_calibracao
                    .map(
                        (p) => `
                            <div class="col-sm-3">
                                <div class="card">
                                    <div class="card-body">
                                        <div class="d-flex w-100 justify-content-between">
                                            <h5 class="mb-1">${p.ponto_descricao}</h5>
                                            <small>
                                                ${p.status_ponto_calibracao == 'ativo' ? 
                                                ' <span class="badge bg-success">Ativo</span>' :
                                                ' <span class="badge bg-danger">Inativo</span>'}
                                            </small>
                                        </div>
                                        <div class="mb-2"><strong>Faixa Nominal:</strong> ${p.ponto_faixa_nominal}</div>
                                        <div class="mb-2"><strong>Unidade:</strong> ${p.ponto_unidade}</div>
                                        <div class="mb-2"><strong>Tolerância Admissível:</strong> ${p.ponto_tolerancia_admissivel}</div>
                                        
                                        <!-- Último Certificado -->
                                        <div class="mb-2"><strong>Último Certificado:</strong> 
                                            ${p.ultimo_certificado === 'reprovado' ? 
                                                '<span class="badge bg-danger">Reprovado</span>' :
                                                p.ultimo_certificado === 'aprovado' ? 
                                                    '<span class="badge bg-success">Aprovado</span>' :
                                                    '<span class="badge bg-warning">Pendente</span>'
                                            }
                                        </div>
            
                                        <div class="mb-2">
                                            ${d.status_calibracao === 'recebido' && p.analise_certificado === null && p.ultimo_envio_pk !== null && p.status_ponto_calibracao == 'ativo' ? 
                                                `<strong>Calibração:</strong> <button class="btn badge btn-danger btn-sm" onclick="analisarCalibracao('${p.ultimo_envio_pk}','${d.tag}','${p.ponto_pk}')">Analisar</button>` :
                                                ``
                                            }
                                        </div>
                                        <div>
                                            ${p.analise_certificado ? 
                                            `<button class="btn badge btn-secondary btn-sm" onclick="ultimaAnalise('${p.ultimo_envio_pk}','${d.tag}','${p.ponto_pk}','${p.ultimo_pdf}')">Última análise</button>`:
                                            `<button class="btn badge btn-secondary btn-sm">Instrumento não possui análise</button>`
                                            }
                                        </div>
                                    </div>
                                </div>
                            </div>
                    `
                    )
                    .join('')}
                </div>
            </div>
        `;
    }
    
});