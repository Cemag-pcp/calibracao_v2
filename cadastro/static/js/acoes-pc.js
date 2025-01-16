function abrirQrCodeModal(tag) {
    fetch(`/instrumento/qrcode/${tag}/`)
        .then(response => response.json())
        .then(data => {

            document.getElementById('modal-title-qrcode').textContent = `QR Code do Instrumento: ${tag}`;
            document.getElementById('modal-body-qrcode').innerHTML = `
                <img src="${data.qrcode_url}" alt="QR Code de ${tag}" class="img-fluid">
            `;
            const modal = new bootstrap.Modal(document.getElementById('modal-qrcode'));
            modal.show();
        })
        .catch(() => alert('Erro ao carregar o QR Code.'));
}

function alterarResponsavel(tag,responsavel_id) {
    toggleRowVisibility(false);

    document.getElementById('form-editar-responsavel').reset();
    document.getElementById('tag-instrumento-responsavel-editar').value = tag;
    console.log(responsavel_id)
    document.getElementById('nome-ultimo-responsavel').value = responsavel_id;

    const modal = new bootstrap.Modal(document.getElementById('modal-alterar-responsavel'));
    modal.show();
}

function toggleRowVisibility(isVisible) {
    const hideRows = document.querySelectorAll('.hide-row');
    hideRows.forEach(row => {
        row.style.visibility = isVisible ? 'visible' : 'hidden';
        row.style.opacity = isVisible ? 1 : 0;
    });
}

document.getElementById('motivo-editar-responsavel').addEventListener('change', function() {
    document.getElementById('col-nome-editar-responsavel').style.visibility = 'visible';
    document.getElementById('col-nome-editar-responsavel').style.opacity = 1;
});

document.getElementById('nome-editar-responsavel').addEventListener('change', function() {
    toggleRowVisibility(this.value !== "");
});


// function abrirHistoricoModal(tag,pontoCalibracao,pontoDescricao) {
//     fetch(`/instrumento/historico/${tag}/${pontoCalibracao}/`)
//         .then(response => response.json())
//         .then(data => {

//             // Atualiza o título do modal
//             document.getElementById('modal-title-historico').textContent = `Histórico do Instrumento: ${tag} - ${pontoDescricao}`;

//             // Seleciona o contêiner do corpo do modal
//             const timelineContainer = document.getElementById('modal-body-historico');

//             // Limpa o conteúdo anterior
//             timelineContainer.innerHTML = '';

//             // Constrói a timeline
//             const timelineHtml = data.historico.map(evento => `
//                 <div class="timeline-event">
//                     <div class="timeline-event-content">
//                         <div class="timeline-event-title">${evento.tipo} - ${evento.data}</div>
//                         <div class="timeline-event-body">${evento.descricao}</div>
//                     </div>
//                 </div>
//             `).join('');

//             // Insere a timeline no modal
//             timelineContainer.innerHTML = `
//                 <div class="timeline">
//                     ${timelineHtml}
//                 </div>
//             `;

//             // Exibe o modal usando Bootstrap
//             const modal = new bootstrap.Modal(document.getElementById('modal-historico'));
//             modal.show();
//         })
//         .catch(error => {
//             console.error('Erro ao carregar o histórico:', error);
//             alert('Erro ao carregar o histórico.');
//         });
// }

function enviarCalibracao(tag,pontoCalibracao) {

    document.getElementById('modal-title-enviar').textContent = `Enviar instrumento: ${tag}`;
    document.getElementById('tag-instrumento-envio').value = tag;
    document.getElementById('pk-ponto-calibracao-enviar').value = pontoCalibracao;
    document.getElementById('formEnviar').reset();

    const modal = new bootstrap.Modal(document.getElementById('modal-enviar'));
    modal.show();

}

function substituicaoInstrumento(tag, responsavel,instrumento_id) {

    document.getElementById('modal-title-enviar').textContent = `Enviar instrumento: ${tag}`;
    document.getElementById('tag-instrumento-status-substituicao').value = instrumento_id;
    let formDevolucao = document.getElementById('statusInstrumentoDevolucao');
    let formSubstituicao = document.getElementById('statusInstrumentoSubstituicao');
    let colInstrumentoStatusSubstituicao = document.querySelectorAll('.col-instrumento-status-substituicao');

    console.log(responsavel)
    if (responsavel === 'null') {
        colInstrumentoStatusSubstituicao.forEach(element => element.classList.add('d-none'));
    } else {
        colInstrumentoStatusSubstituicao.forEach(element => element.classList.remove('d-none'));
    }
    
    formDevolucao.classList.add('d-none');
    formDevolucao.reset();
    formSubstituicao.classList.remove('d-none');
    formSubstituicao.reset();

    document.getElementById('tag-instrumento-envio').value = tag;
    document.getElementById('statusInstrumentoModalLabel').textContent = "Deseja confirmar a substituição do instrumento " + tag + " ?";
    let responsavelStatus = document.getElementById('responsavel-status-substituicao');
    let instrumentoStatus = document.getElementById('instrumento-status-substituicao');

    responsavelStatus.value = responsavel;

    for (let option of instrumentoStatus.options) { 
        if (option.value === tag) {
            option.style.display = 'none';
        } else {
            option.style.display = 'block';
        }
    }

    console.log(document.getElementById('responsavel-status-substituicao').value)

    const modal = new bootstrap.Modal(document.getElementById('statusInstrumentoModal'));
    modal.show();

}

// function devolucaoInstrumento(tag,responsavel) {

//     document.getElementById('modal-title-enviar').textContent = `Enviar instrumento: ${tag}`;
//     let formDevolucao = document.getElementById('statusInstrumentoDevolucao');
//     let formSubstituicao = document.getElementById('statusInstrumentoSubstituicao');
    
//     formDevolucao.classList.remove('d-none');
//     formDevolucao.reset();
//     formSubstituicao.classList.add('d-none');
//     formSubstituicao.reset();

//     document.getElementById('tag-instrumento-envio').value = tag;
//     document.getElementById('statusInstrumentoModalLabel').textContent = "Deseja confirmar a devolução do instrumento " + tag + " ?";
    
//     document.getElementById('responsavel-status-devolucao').value = responsavel;

//     const modal = new bootstrap.Modal(document.getElementById('statusInstrumentoModal'));
//     modal.show();

// }

function receberCalibracao(idsEnvio, tag) {
    document.getElementById('modal-title-recebimento').textContent = `Recebimento do instrumento: ${tag}`;
    console.log(idsEnvio)
    document.getElementById('id-instrumento-recebimento').value = idsEnvio; // Transformando a lista em string
    document.getElementById('formRecebimento').reset();

    const modal = new bootstrap.Modal(document.getElementById('modal-recebimento'));
    modal.show();
}


function analisarCalibracao(idEnvio,tag,pontoCalibracao) {

    document.getElementById('modal-title-analise').textContent = `Analisar: ${tag}`;
    document.getElementById('id-instrumento-analise').value = idEnvio;
    document.getElementById('formAnalise').reset();

    buscarInfoInstrumento(idEnvio,pontoCalibracao)

}

function ultimaAnalise(idEnvio,tag,pontoCalibracao) {

    document.getElementById('modal-title-ultima-analise').textContent = `Analisar: ${tag}`;
    document.getElementById('id-instrumento-ultima-analise').value = idEnvio;
    document.getElementById('formUltimaAnalise').reset();

    buscarUltimaAnaliseInstrumento(idEnvio,pontoCalibracao)

}

document.addEventListener('DOMContentLoaded', () => {

    // Seleciona o formulário
    const formEnviar = document.getElementById('formEnviar');
    const formRecebimento = document.getElementById('formRecebimento');
    const formAnalise = document.getElementById('formAnalise');
    const formStatusInstrumento = document.getElementById('statusInstrumentoSubstituicao');

    // Captura o evento de envio do formulário
    formEnviar.addEventListener('submit', async (event) => {
        event.preventDefault(); // Impede o envio padrão do formulário

        // Cria o objeto com os dados do formulário
        const formData = new FormData(formEnviar);

        // Converte os dados do formulário para JSON
        const jsonData = {};
        formData.forEach((value, key) => {
            jsonData[key] = value;
        });

        try {

            // Envia a requisição para o backend
            const response = await fetch('/enviar-calibracao/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(), // Obtém o CSRF Token
                },
                body: JSON.stringify(jsonData), // Dados em JSON
            });
    
            if (response.ok) {
                // Exibe uma mensagem de sucesso usando SweetAlert
                
                const data = await response.json(); // Parse da resposta JSON

                Swal.fire({
                    icon: 'success',
                    title: 'Sucesso!',
                    text: data.message,
                });
    
                $('#instrumentos-table').DataTable().ajax.reload(); // Reatualiza a tabela

                const modal = bootstrap.Modal.getInstance(document.getElementById('modal-enviar'));
                modal.hide();

            } else {

                const errorData = await response.json(); // Parse da resposta JSON

                // Exibe uma mensagem de erro usando SweetAlert
                Swal.fire({
                    icon: 'error',
                    title: 'Erro!',
                    text: errorData.message || 'Algo deu errado, tente novamente.',
                });
            }
        } catch (error) {
            console.error('Erro na requisição:', error);
            // Exibe uma mensagem de erro genérica em caso de falha na requisição
            Swal.fire({
                icon: 'error',
                title: 'Erro de Conexão',
                text: 'Erro ao enviar o formulário. Verifique sua conexão e tente novamente.',
            });
        }
    });

    // Captura o evento de envio do formulário
    formRecebimento.addEventListener('submit', async (event) => {
        event.preventDefault(); // Impede o envio padrão do formulário

        // Cria o objeto com os dados do formulário
        const formData = new FormData(formRecebimento);

        // Converte os dados do formulário para JSON
        const jsonData = {};
        formData.forEach((value, key) => {
            jsonData[key] = value;
        });

        console.log(jsonData)

        try {
            // Envia a requisição para o backend
            const response = await fetch('/receber-calibracao/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(), // Obtém o CSRF Token
                },
                body: JSON.stringify(jsonData), // Dados em JSON
            });

            if (response.ok) {
                const data = await response.json(); // Parse da resposta JSON

                // Exibe uma mensagem de sucesso usando SweetAlert
                Swal.fire({
                    icon: 'success',
                    title: 'Sucesso!',
                    text: data.message,
                });

                $('#instrumentos-table').DataTable().ajax.reload(); // Reatualiza a tabela

                const modal = bootstrap.Modal.getInstance(document.getElementById('modal-recebimento'));
                modal.hide();
            
            } else {
                // Exibe uma mensagem de erro usando SweetAlert
                Swal.fire({
                    icon: 'error',
                    title: 'Erro!',
                    text: data.message || 'Algo deu errado, tente novamente.',
                });
            }

        } catch (error) {
            const errorData = await response.json();
            // Exibe uma mensagem de erro genérica em caso de falha na requisição
            Swal.fire({
                icon: 'error',
                title: 'Erro de Conexão',
                text: errorData.message || 'Algo deu errado, tente novamente.',
            });
        }
    });

    // Captura o evento de envio do formulário
    formAnalise.addEventListener('submit', async (event) => {
        event.preventDefault(); // Impede o envio padrão do formulário

        // Cria o objeto com os dados do formulário
        const formData = new FormData(formAnalise);

        // Converte os dados do formulário para JSON
        const jsonData = {};
        formData.forEach((value, key) => {
            jsonData[key] = value;
        });

        try {
            // Envia a requisição para o backend
            const response = await fetch('/analisar-calibracao/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(), // Obtém o CSRF Token
                },
                body: JSON.stringify(jsonData), // Dados em JSON
            });

            if (response.ok) {
                const data = await response.json(); // Parse da resposta JSON

                // Exibe uma mensagem de sucesso usando SweetAlert
                Swal.fire({
                    icon: 'success',
                    title: 'Sucesso!',
                    text: data.message || 'Operação concluída com sucesso!',
                });

                $('#instrumentos-table').DataTable().ajax.reload(); // Reatualiza a tabela

                // Fecha o modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('modal-analise'));
                modal.hide();

            } else {
                const errorData = await response.json();
                // Exibe uma mensagem de erro usando SweetAlert
                Swal.fire({
                    icon: 'error',
                    title: 'Erro!',
                    text: errorData.message || 'Algo deu errado, tente novamente.',
                });
            }

        } catch (error) {
            console.error('Erro na requisição:', error);
            // Exibe uma mensagem de erro genérica em caso de falha na requisição
            Swal.fire({
                icon: 'error',
                title: 'Erro de Conexão',
                text: 'Erro ao enviar o formulário. Verifique sua conexão e tente novamente.',
            });
        }
    });

    formStatusInstrumento.addEventListener('submit', async (event) => {
        event.preventDefault(); // Impede o envio padrão do formulário
         // Cria o objeto com os dados do formulário
         const formData = new FormData(formStatusInstrumento);

         // Converte os dados do formulário para JSON
         const jsonData = {};
         formData.forEach((value, key) => {
             jsonData[key] = value;
         });

         console.log(formData)

         console.log(jsonData)
 
         try {
             // Envia a requisição para o backend
             const response = await fetch('/substituir-instrumento/', {
                 method: 'POST',
                 headers: {
                     'Content-Type': 'application/json',
                     'X-CSRFToken': getCsrfToken(), // Obtém o CSRF Token
                 },
                 body: JSON.stringify(jsonData), // Dados em JSON
             });
 
             if (response.ok) {
                 const data = await response.json(); // Parse da resposta JSON
 
                 // Exibe uma mensagem de sucesso usando SweetAlert
                 Swal.fire({
                     icon: 'success',
                     title: 'Sucesso!',
                     text: data.message || 'Operação concluída com sucesso!',
                 });
 
                 $('#instrumentos-table').DataTable().ajax.reload(); // Reatualiza a tabela
 
                 // Fecha o modal
                 const modal = bootstrap.Modal.getInstance(document.getElementById('modal-analise'));
                 modal.hide();
 
             } else {
                 const errorData = await response.json();
                 // Exibe uma mensagem de erro usando SweetAlert
                 Swal.fire({
                     icon: 'error',
                     title: 'Erro!',
                     text: errorData.message || 'Algo deu errado, tente novamente.',
                 });
             }
 
         } catch (error) {
             console.error('Erro na requisição:', error);
             // Exibe uma mensagem de erro genérica em caso de falha na requisição
             Swal.fire({
                 icon: 'error',
                 title: 'Erro de Conexão',
                 text: 'Erro ao enviar o formulário. Verifique sua conexão e tente novamente.',
             });
         }
    })
});

// Função para obter o CSRF Token do cookie
function getCsrfToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find((row) => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

function buscarInfoInstrumento(idEnvio, pontoCalibracao) {
    fetch(`/instrumento/info/${pontoCalibracao}/${idEnvio}/`)
        .then(response => response.json())
        .then(data => {
            // Atualiza as informações do instrumento
            document.getElementById('faixaNominal').textContent = data.info[0].faixa_nominal || 'Não disponível';
            document.getElementById('toleranciaAdmissivel').textContent = data.info[0].tol_admissivel || 'Não disponível';

            // Atualiza o link do certificado
            const certificadoLink = document.getElementById('certificadoAtual');
            if (data.info[0].certificado) {
                certificadoLink.textContent = 'Visualizar Certificado';
                certificadoLink.href = data.info[0].certificado;
                certificadoLink.target = '_blank'; // Abre o link em uma nova aba
                certificadoLink.rel = 'noopener noreferrer'; // Melhora a segurança
            } else {
                certificadoLink.textContent = 'Não disponível';
                certificadoLink.href = '#'; // Define como um link não funcional
            }

            const modal = new bootstrap.Modal(document.getElementById('modal-analise'));
            modal.show();
        
        })
        .catch(error => {
            console.error('Erro ao carregar as informações do instrumento:', error);
            alert('Erro ao carregar as informações do instrumento.');
        });
}

function buscarUltimaAnaliseInstrumento(idEnvio, pontoCalibracao) {
    fetch(`/instrumento/info/ultima_analise/${pontoCalibracao}/${idEnvio}/`)
        .then(response => response.json())
        .then(data => {
            const info = data.info[0];
            const analise = info.analise_certificado;

            console.log(analise.tendencia)

            // Preenchendo os campos do modal
            document.getElementById('id-instrumento-ultima-analise').value = pontoCalibracao; // Ou outro identificador relevante
            document.getElementById('incertezaUltimaAnalise').value = analise.incerteza;
            document.getElementById('tendeciaUltimaAnalise').value = analise.tendencia;
            document.getElementById('dataUltimaAnalise').value = analise.data_analise;
            document.getElementById('resultadoUltimaAnalise').value = analise.analise_certificado; // Supondo que este valor seja "aprovado" ou "reprovado"

            // Preenchendo as informações do instrumento
            document.getElementById('faixaNominalUltimaAnalise').textContent = info.ponto_calibracao.faixa_nominal;
            document.getElementById('toleranciaAdmissivelUltimaAnalise').textContent = info.ponto_calibracao.tol_admissivel;

            const modalElement = document.getElementById('modal-ultima-analise');
            const modal = new bootstrap.Modal(modalElement);
            // Exibe o modal
            modal.show();
        })
        .catch(error => {
            console.error('Erro ao carregar as informações do instrumento:', error);
            alert('Erro ao carregar as informações do instrumento.');
        });
}

function abrirModalEscolherResponsavel(tag) {

    document.getElementById('modal-title-responsavel').textContent = `Escolher responsável para: ${tag}`;
    document.getElementById('tag-instrumento-responsavel').value = tag;
    document.getElementById('formResponsavel').reset();

    document.getElementById('formResponsavel').style.visibility = 'visible';
    document.getElementById('formResponsavel').style.opacity = '1';
    document.getElementById('formResponsavel').style.position = 'relative';

    // Exibe o formulário de visualização
    document.getElementById('form-visualizar-ficha').style.visibility = 'hidden';
    document.getElementById('form-visualizar-ficha').style.opacity = '0';
    document.getElementById('form-visualizar-ficha').style.position = 'absolute';

    var canvas = document.getElementById('signature-canvas');
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const modal = new bootstrap.Modal(document.getElementById('modal-responsavel'));
    modal.show();
}

function visualizarResponsavel(tag, responsavel_id, data_entrega) {

    document.getElementById('modal-title-responsavel').textContent = `Responsável do instrumento: ${tag}`;
    document.getElementById('tag-instrumento-responsavel').value = tag;
    document.getElementById('formResponsavel').reset();

    document.getElementById('nome-responsavel-visualizar-ficha').value = responsavel_id;
    document.getElementById('dataEntrega-visualizar-ficha').value = data_entrega;

    document.getElementById('formResponsavel').style.visibility = 'hidden';
    document.getElementById('formResponsavel').style.opacity = '0';
    document.getElementById('formResponsavel').style.position = 'absolute';

    // Exibe o formulário de visualização
    document.getElementById('form-visualizar-ficha').style.visibility = 'visible';
    document.getElementById('form-visualizar-ficha').style.opacity = '1';
    document.getElementById('form-visualizar-ficha').style.position = 'relative';

    var canvas = document.getElementById('signature-canvas');
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const modal = new bootstrap.Modal(document.getElementById('modal-responsavel'));
    modal.show();

}