const table = $('#instrumentos-table').DataTable({
    processing: true,
    serverSide: true,
    pageLength: 10, // Itens por pÃ¡gina
    lengthMenu: [[10, 25, 50], [10, 25, 50]], // OpÃ§Ãµes de paginação
    ajax: {
        url: '/instrumentos-data/',
        type: 'GET',
        data: function (d) {
            // Adicionar os parÃ¢metros de filtro ao DataTables
            d.tag = $('#pesquisar-tag-calibracao').val();
            d.tipo = $('#pesquisar-tipo-calibracao').val();
            d.necessita_calibrar = $('#filtro-obrigacao-calibracao').val();
            
            // Status do instrumento
            let statusInstrumento = [];
            document.querySelectorAll('input[name^="status_instrumento_"]:checked').forEach(checkbox => {
                statusInstrumento.push(checkbox.value);
            });
            d.status_instrumento = statusInstrumento.join(',');
            // Status da calibração
            let statusCalibracao = [];
            document.querySelectorAll('input[name^="status_calibracao_"]:checked').forEach(checkbox => {
                statusCalibracao.push(checkbox.value);
            });
            d.status_calibracao = statusCalibracao.join(',');
            
            // Datas de última calibração
            d.data_ultima_inicio = $('#data-ultima-calibracao-inicio').val();
            d.data_ultima_fim = $('#data-ultima-calibracao-fim').val();
            
            // Datas de próxima calibração
            d.data_proxima_inicio = $('#data-proxima-calibracao-inicio').val();
            d.data_proxima_fim = $('#data-proxima-calibracao-fim').val();
        },
        dataSrc: function (json) {
            $('#qtd-pendente-calibracao').html(`Quantidade Total: ${json.recordsTotal}`);
            $('#qtd-filtrada-calibracao').html(`Quantidade Filtrada: ${json.recordsFiltered}`).show();
            return json.data;
        }
    },
    columns: [
        {
            className: 'details-control',
            orderable: false,
            data: null,
            defaultContent: '<i class="fa fa-plus-circle text-primary" title="Expandir"></i>',
        },
        { data: 'tag', title: 'Tag', orderable: true},
        { data: 'tipo_instrumento', title: 'Tipo de Instrumento'},
        { 
            data: 'status_instrumento',
            title: 'Status',
            orderable: true, 
            render: function(data, type, row) {
                console.log(row.status_instrumento);
                if (row.status_instrumento === 'Aguardando retornar da calibração') {
                    return `<span class="badge bg-success">Aguardando retornar da calibração</span>`;
                } else if (row.status_instrumento === 'ativo') {
                    return `<span class="badge bg-success">Disponí­vel</span>`;
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
        { 
            data: 'ultima_calibracao',
            title: 'Última Calibração',

        },
        {   
            data: 'proxima_calibracao',
            title: 'Próxima Calibração',
            orderable: false,
            render: function(data, type, row) {
                if (row.status_instrumento === 'danificado') {
                    return `N/A`;
                } else {
                    return `${row.proxima_calibracao}`;
                }
            }

         },
        {
            data: 'status_calibracao_string',
            title: 'Status da Calibração',
            orderable: false,
            render: function(data, type, row) {
                console.log("status_calibração: ", row.status_calibracao_string);
                if (row.status_calibracao_string === 'Atrasado') {
                    return `<span class="badge bg-danger">Atrasado!</span>`;
                } else if (row.status_calibracao_string === 'Em calibração') {
                    return `<span class="badge bg-primary">Em calibração</span>`;
                } else if (row.status_calibracao_string === 'A analisar') {
                    return `<span class="badge bg-secondary">A analisar</span>`;
                } else if (row.status_calibracao_string === 'Em dia') {
                    return `<span class="badge bg-success">Calibrado</span>`;
                } else {
                    return `N/A`;
                }
            }

        },
        {
            data: null,
            orderable: false,
            render: function (data, type, row) {
                // Exibe placeholder até a resposta da API
                return `<span id="responsavel-${row.id}">
                            <button class="btn btn-light btn-sm" disabled>Carregando...</button>
                        </span>`;
            },
            createdCell: function (td, cellData, rowData, row, col) {
                // Faz a chamada dinÃ¢mica após o carregamento da linha
                fetch(`/api/responsavel/${rowData.id}/`)  // Exemplo: rota Django que retorna JSON do responsável
                    .then(response => response.json())
                    .then(resp => {
                        const el = document.getElementById(`responsavel-${rowData.id}`);
                        if (!el) return;

                        if (rowData.status_calibracao === 'enviado') {
                            el.innerHTML = '';  // nÃ£o mostra nada
                        } else if (!resp.matriculaNome) {
                            el.innerHTML = `<button class="btn badge btn-secondary btn-sm"
                                onclick="abrirModalEscolherResponsavel('${rowData.tag}')">
                                Escolher responsável
                            </button>`;
                        } else {
                            el.innerHTML = `<span class="btn badge btn-primary"
                                onclick="visualizarResponsavel('${rowData.tag}',
                                                            '${resp.id}',
                                                            '${resp.dataEntrega}')">
                                ${resp.matriculaNome}
                            </span>`;
                        }
                    })
                    .catch(() => {
                        const el = document.getElementById(`responsavel-${rowData.id}`);
                        if (el) el.innerHTML = `<span class="badge bg-danger">Erro</span>`;
                    });
            }
        },
        {
            data: null, 
            orderable: false, 
            defaultContent: '<div class="text-center"><i class="fa fa-spinner fa-spin"></i></div>',
            createdCell: function (td, cellData, rowData, row, col) {
                const cellId = `acoes-${rowData.id}`;
                $(td).attr('id', cellId);

                // Buscar dados da API
                fetch(`/api/instrumentos/${rowData.id}/detalhes/`)
                    .then(r => r.json())
                    .then(data => {
                        console.log("data: ", data);
                        const html = gerarDropdownAcoes(data);
                        document.getElementById(cellId).innerHTML = html;
                    })
                    .catch(() => {
                        document.getElementById(cellId).innerHTML = `<span class="badge bg-danger">Cadastre um ponto</span>`;
                    });
            }
        },
    ],
    responsive: true,
    autoWidth: false,       // Desativa ajuste automÃ¡tico da largura das colunas
    searching: false,
    order: [[4, 'asc'], [1, 'asc']],
});

function gerarDropdownAcoes(row) {
    const ultimoEnvioList = row.pontos_calibracao.map(ponto => ponto.ultimo_envio_pk);

    // Filtra os pontos onde ultimo_envio_pk nÃ£o é null e mapeia os analise_certificado
    const analise_certificados = row.pontos_calibracao
        .filter(ponto => ponto.ultimo_envio_pk !== null)
        .map(ponto => ponto.analise_certificado);

    const contem_null = analise_certificados.some(certificado => certificado === null);
    const todos_certificados_true = analise_certificados.every(certificado => certificado === true);

    let buttons = `
        <div class="dropdown text-center">
            <a data-bs-toggle="dropdown" aria-expanded="false" style="cursor:pointer;">
                <i class="fa-solid fa-angle-down" style="color:black;"></i>
            </a>
            <ul class="dropdown-menu">
                <li><p class="dropdown-header">Histórico</p></li>
                <li><a class="dropdown-item" style="cursor:pointer" onclick="abrirQrCodeModal('${row.tag}')">
                    Ver QR Code
                </a></li>
    `;

    // OpÃ§Ãµes de â€œItemâ€
    if (row.status_calibracao !== 'enviado' && row.status_instrumento !== 'danificado') {
        buttons += `
            <li><hr class="dropdown-divider"></li>
            <li><p class="dropdown-header">Item</p></li>`;

        if (row.responsavel && row.responsavel.id !== null) {
            buttons += `
                <li>
                    <a class="dropdown-item" style="cursor:pointer"
                        responsavel-id="${row.responsavel.id}"
                        onclick="alterarResponsavel('${row.tag}','${row.responsavel.id}')">
                        Alterar responsável
                    </a>
                </li>`;
        }

        buttons += `
            <li>
                <a class="dropdown-item" style="cursor:pointer"
                    onclick="substituicaoInstrumento('${row.tag}','${row.responsavel?.id ?? ''}','${row.id}')">
                    Danificado
                </a>
            </li>`;
    }

    // Status â€œEm calibração / recebido / anÃ¡lise / enviarâ€
    console.log(row.status_calibracao);
    if (row.status_calibracao === 'enviado') {
        buttons += `
            <li><hr class="dropdown-divider"></li>
            <li><p class="dropdown-header">Status: A Receber</p></li>
            <li>
                <a class="dropdown-item" style="cursor:pointer"
                    onclick="receberCalibracao('${JSON.stringify(ultimoEnvioList)}', '${row.tag}', '${row.ultimo_assinante?.nome ?? ''}')">
                    Receber
                </a>
            </li>`;
    } else if (row.status_calibracao === 'recebido' && contem_null) {
        buttons += `
            <li><hr class="dropdown-divider"></li>
            <li><p class="dropdown-header">Status: A Analisar</p></li>`;
    } else if (row.status_calibracao === 'recebido' && todos_certificados_true) {
        buttons += `
            <li><hr class="dropdown-divider"></li>
            <li><p class="dropdown-header">Status: A Enviar</p></li>
            <li>
                <a class="dropdown-item" style="cursor:pointer"
                    onclick="enviarCalibracao('${row.tag}','${row.pontos_calibracao[0]?.ponto_pk ?? ''}','${row.responsavel?.matriculaNome ?? ''}')">
                    Enviar
                </a>
            </li>`;
    } else {
        buttons += `
            <li><hr class="dropdown-divider"></li>
            <li><p class="dropdown-header">Status: A Enviar</p></li>
            <li>
                <a class="dropdown-item" style="cursor:pointer"
                    onclick="enviarCalibracao('${row.tag}','${row.pontos_calibracao[0]?.ponto_pk ?? ''}','${row.responsavel?.matriculaNome ?? ''}')">
                    Enviar
                </a>
            </li>`;
    }

    buttons += `
            </ul>
        </div>`;
    return buttons;
}

$('#instrumentos-table tbody').on('click', 'td.details-control', function () {
    const tr = $(this).closest('tr');
    const row = table.row(tr);

    if (row.child.isShown()) {
        // Fecha o painel
        row.child.hide();
        tr.removeClass('shown');
    } else {
        // Mostra loading enquanto busca
        row.child('<div class="p-2 text-center"><i class="fa fa-spinner fa-spin"></i> Carregando detalhes...</div>').show();
        tr.addClass('shown');

        // Chama a API para buscar os detalhes completos
        fetch(`/api/instrumentos/${row.data().id}/detalhes/`)
            .then(res => {
                if (!res.ok) throw new Error('Cadastre um ponto de calibração!');
                return res.json();
            })
            .then(data => {
                // Usa a função format() que vocÃª jÃ¡ tem
                row.child(format(data)).show();
            })
            .catch(err => {
                row.child(`<div class="p-2 text-danger">Erro: ${err.message}</div>`).show();
            });
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
                                    <div class="mb-2"><strong>TolerÃ¢ncia AdmissÃ­vel:</strong> ${p.ponto_tolerancia_admissivel}</div>
                                    
                                    <!-- último Certificado -->
                                    <div class="mb-2"><strong>último Certificado:</strong> 
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
                                        `<button class="btn badge btn-secondary btn-sm" onclick="ultimaAnalise('${p.ultimo_envio_pk}','${d.tag}','${p.ponto_pk}','${p.ultimo_pdf}')">última anÃ¡lise</button>`:
                                        `<button class="btn badge btn-secondary btn-sm">Instrumento nÃ£o possui anÃ¡lise</button>`
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

// Adicionar evento para o botÃ£o de filtrar
$('#btn-filtrar-calibracao').on('click', function() {
    table.ajax.reload(); // Recarrega os dados com os novos filtros
    
    // Atualizar os spans de filtros aplicados (similar ao código anterior)
    atualizarFiltrosAplicados();
});

// Adicionar evento para o botÃ£o de limpar
$('#btn-limpar-calibracao').on('click', function() {
    // Limpar todos os campos de filtro
    $('#pesquisar-tag-calibracao').val('');
    $('#pesquisar-tipo-calibracao').val('');
    $('input[name^="status_instrumento_"]').prop('checked', false);
    $('input[name^="status_calibracao_"]').prop('checked', false);
    $('#data-ultima-calibracao-inicio').val('');
    $('#data-ultima-calibracao-fim').val('');
    $('#data-proxima-calibracao-inicio').val('');
    $('#data-proxima-calibracao-fim').val('');
    $('#filtro-obrigacao-calibracao').val('');
    
    // Recarregar a tabela sem filtros
    table.ajax.reload();
    
    // Esconder todos os spans de filtros aplicados
    $('[id^="itens-filtrados-calibracao-"]').hide();
});

function atualizarFiltrosAplicados() {
    // Tag
    if ($('#pesquisar-tag-calibracao').val()) {
        $('#itens-filtrados-calibracao-tag').text('Tag: ' + $('#pesquisar-tag-calibracao').val()).show();
    } else {
        $('#itens-filtrados-calibracao-tag').hide();
    }
    
    // Tipo
    if ($('#pesquisar-tipo-calibracao').val()) {
        $('#itens-filtrados-calibracao-tipo').text('Tipo: ' + $('#pesquisar-tipo-calibracao').val()).show();
    } else {
        $('#itens-filtrados-calibracao-tipo').hide();
    }
    
    // Status Instrumento
    let statusInstrumento = [];
    $('input[name^="status_instrumento_"]:checked').each(function() {
        statusInstrumento.push($(this).next('label').text());
    });
    if (statusInstrumento.length > 0) {
        $('#itens-filtrados-calibracao-status-instrumento').text('Status Instrumento: ' + statusInstrumento.join(', ')).show();
    } else {
        $('#itens-filtrados-calibracao-status-instrumento').hide();
    }
    
    // Status Calibração
    let statusCalibracao = [];
    $('input[name^="status_calibracao_"]:checked').each(function() {
        statusCalibracao.push($(this).next('label').text());
    });
    if (statusCalibracao.length > 0) {
        $('#itens-filtrados-calibracao-status-calibracao').text('Status Calibração: ' + statusCalibracao.join(', ')).show();
    } else {
        $('#itens-filtrados-calibracao-status-calibracao').hide();
    }
        
    // Obrigatoriedade de calibracao
    const obrig = $("#filtro-obrigacao-calibracao").val();
    if (obrig === "true") {
        $("#itens-filtrados-calibracao-obrigacao").text("Obrigatoriedade: Obrigatório calibrar").show();
    } else if (obrig === "false") {
        $("#itens-filtrados-calibracao-obrigacao").text("Obrigatoriedade: Não obrigatório calibrar").show();
    } else {
        $("#itens-filtrados-calibracao-obrigacao").hide();
    }
    
    // Obrigatoriedade de calibração
    if (obrig === 'true') {
    } else if (obrig === 'false') {
    } else {
    }
    if (obrig === 'true') {
    } else if (obrig === 'false') {
    } else {
    }

    // Data última Calibração
    if ($('#data-ultima-calibracao-inicio').val() && $('#data-ultima-calibracao-fim').val()) {
        $('#itens-filtrados-calibracao-data-ultima').text(
            'última Calibração: ' + $('#data-ultima-calibracao-inicio').val() + ' até ' + $('#data-ultima-calibracao-fim').val()
        ).show();
    } else {
        $('#itens-filtrados-calibracao-data-ultima').hide();
    }
    
    if ($('#data-proxima-calibracao-inicio').val() && $('#data-proxima-calibracao-fim').val()) {
        $('#itens-filtrados-calibracao-data-proxima').text(
            'Próxima Calibração: ' + $('#data-proxima-calibracao-inicio').val() + ' até ' + $('#data-proxima-calibracao-fim').val()
        ).show();
    } else {
        $('#itens-filtrados-calibracao-data-proxima').hide();
    }
}

$(document).ready(function () {
    table.ajax.reload();
})




