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

function abrirHistoricoModal(tag,pontoCalibracao,pontoDescricao) {
    fetch(`/instrumento/historico/${tag}/${pontoCalibracao}/`)
        .then(response => response.json())
        .then(data => {

            // Atualiza o título do modal
            document.getElementById('modal-title-historico').textContent = `Histórico do Instrumento: ${tag} - ${pontoDescricao}`;

            // Seleciona o contêiner do corpo do modal
            const timelineContainer = document.getElementById('modal-body-historico');

            // Limpa o conteúdo anterior
            timelineContainer.innerHTML = '';

            // Constrói a timeline
            const timelineHtml = data.historico.map(evento => `
                <div class="timeline-event">
                    <div class="timeline-event-content">
                        <div class="timeline-event-title">${evento.tipo} - ${evento.data}</div>
                        <div class="timeline-event-body">${evento.descricao}</div>
                    </div>
                </div>
            `).join('');

            // Insere a timeline no modal
            timelineContainer.innerHTML = `
                <div class="timeline">
                    ${timelineHtml}
                </div>
            `;

            // Exibe o modal usando Bootstrap
            const modal = new bootstrap.Modal(document.getElementById('modal-historico'));
            modal.show();
        })
        .catch(error => {
            console.error('Erro ao carregar o histórico:', error);
            alert('Erro ao carregar o histórico.');
        });
}

function enviarCalibracao(tag,pontoCalibracao) {

    document.getElementById('modal-title-enviar').textContent = `Enviar instrumento: ${tag}`;
    document.getElementById('tag-instrumento-envio').value = tag;
    document.getElementById('pk-ponto-calibracao-enviar').value = pontoCalibracao;
    document.getElementById('formEnviar').reset();

    const modal = new bootstrap.Modal(document.getElementById('modal-enviar'));
    modal.show();

}

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

document.addEventListener('DOMContentLoaded', () => {

    // Seleciona o formulário
    const formEnviar = document.getElementById('formEnviar');
    const formRecebimento = document.getElementById('formRecebimento');
    const formAnalise = document.getElementById('formAnalise');
    const formResponsavel = document.getElementById('formResponsavel');

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

    // Captura o evento de envio do formulário
    formResponsavel.addEventListener('submit', async (event) => {
        event.preventDefault(); // Impede o envio padrão do formulário

        // Cria o objeto com os dados do formulário
        const formData = new FormData(formResponsavel);

        // Converte os dados do formulário para JSON
        const jsonData = {};
        formData.forEach((value, key) => {
            jsonData[key] = value;
        });

        try {
            // Envia a requisição para o backend
            const response = await fetch('/escolher-responsavel/', {
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
                const modal = bootstrap.Modal.getInstance(document.getElementById('modal-responsavel'));
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

function abrirModalEscolherResponsavel(tag) {
    document.getElementById('modal-title-responsavel').textContent = `Escolher responsável para: ${tag}`;
    document.getElementById('tag-instrumento-responsavel').value = tag;
    document.getElementById('formResponsavel').reset();

    const modal = new bootstrap.Modal(document.getElementById('modal-responsavel'));
    modal.show();

}