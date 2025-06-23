function abrirQrCodeModal(tag) {
    Swal.fire({
        title: 'Carregando...',
        text: 'Buscando QRCode...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });
    fetch(`/instrumento/qrcode/${tag}/`)
        .then(response => response.json())
        .then(data => {
            Swal.close();
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
    document.getElementById('select2-nome-editar-responsavel-container').textContent = "Controle da Qualidade";
    document.getElementById('nome-ultimo-responsavel').value = responsavel_id;
    const selectResponsaveis = document.getElementById('nome-editar-responsavel')

    for (let option of selectResponsaveis.options) {
        if (option.value == responsavel_id) {
            option.remove()   
        }
    }

    document.getElementById('tag-instrumento-responsavel-editar').value = tag;

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

$(document).on('change.select2', '#nome-editar-responsavel', function() {
    toggleRowVisibility(this.value !== "");
});

function enviarCalibracao(tag,pontoCalibracao,nomeResponsavel) {

    document.getElementById('modal-title-enviar').textContent = `Enviar instrumento: ${tag}`;
    document.getElementById('col-instrumento-substituira-envio').style.display = 'none';
    document.getElementById('tag-instrumento-envio').value = tag;
    document.getElementById('pk-ponto-calibracao-enviar').value = pontoCalibracao;
    document.getElementById('select2-responsavelEnvio-container').textContent = '------------';

    document.getElementById('formEnviar').reset();
    let novoInstrumento = document.getElementById('instrumento-substituira-envio');
    let campoParaSubstituirInstrumento = document.getElementById('campo-novo-instrumento');
    
    if (nomeResponsavel !== 'null') {
        campoParaSubstituirInstrumento.style.display = 'block';
        document.getElementById('descricao-instrumento-substituido').innerHTML = `Atualmente, <strong>${nomeResponsavel}</strong> está responsável pelo instrumento <strong>${tag}</strong>. Gostaria de designar um novo instrumento para ele?`;
    } else {
        campoParaSubstituirInstrumento.style.display = 'none';
    }

    carregarInstrumentosNoSelect(novoInstrumento,tag);

    const modal = new bootstrap.Modal(document.getElementById('modal-enviar'));
    modal.show();

}

document.getElementById('validacao-de-substituicao').addEventListener('change', function() {
    var substituicaoEnvio = document.getElementById('col-instrumento-substituira-envio');
    if (this.value === 'Sim') {
        substituicaoEnvio.style.display = 'block';
        document.getElementById('instrumento-substituira-envio').required = true;
    } else {
        substituicaoEnvio.style.display = 'none';
        document.getElementById('instrumento-substituira-envio').required = false;
    }
});

function substituicaoInstrumento(tag, responsavel, instrumento_id) {
    document.getElementById('modal-title-enviar').textContent = `Enviar instrumento: ${tag}`;
    document.getElementById('tag-instrumento-status-substituido').value = instrumento_id;
    let formDevolucao = document.getElementById('statusInstrumentoDevolucao');
    let formSubstituicao = document.getElementById('statusInstrumentoSubstituicao');
    let colInstrumentoStatusSubstituicao = document.querySelectorAll('.col-instrumento-status-substituicao');
    let instrumentoStatusSubstituicao = document.getElementById("instrumento-status-substituicao");
    let responsavel_id = document.getElementById('responsavel-id');
    responsavel_id.value = responsavel;

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
    document.getElementById('statusInstrumentoModalLabel').textContent = `Deseja confirmar a substituição do instrumento ${tag} ?`;
    let responsavelStatus = document.getElementById('responsavel-status-substituicao');
    let instrumentoStatus = document.getElementById('instrumento-status-substituicao');

    responsavelStatus.value = responsavel;

    carregarInstrumentosNoSelect(instrumentoStatus,tag) 

    const modal = new bootstrap.Modal(document.getElementById('statusInstrumentoModal'));
    modal.show();
}

function carregarInstrumentosNoSelect(selectInstrumentos,tag) {
    // Fetching all instruments
    fetch('/substituir-instrumento/')
    .then(response => response.json())
    .then(data => {
        // Populate the instrument options dynamically if needed
        selectInstrumentos.innerHTML = ''; // Clear existing options
        let option = document.createElement('option');
        option.value = '';
        option.textContent = 'Nenhum';
        selectInstrumentos.appendChild(option);
        data.forEach(instrument => {
            let option = document.createElement('option');
            option.value = instrument.id;
            option.textContent = instrument.tag;
            if (instrument.tag === tag) {
                option.style.display = 'none'; // Hide current instrument
            }
            selectInstrumentos.appendChild(option);
        });
    })
    .catch(error => console.error('Error fetching instruments:', error));
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

// }s

function receberCalibracao(idsEnvio, tag, ultimoAssinanteNome) {
    let divUltimoAssinante = document.getElementById('campo-ultimo-assinante');

    document.getElementById('modal-title-recebimento').textContent = `Recebimento do instrumento: ${tag}`;

    document.getElementById('descricao-ultimo-assinante').innerHTML = `O último responsável pelo instrumento <strong>${tag}</strong> foi o funcionário <strong>${ultimoAssinanteNome}</strong>`;

    ultimoAssinanteNome === 'null' ? divUltimoAssinante.style.display = 'none': divUltimoAssinante.style.display = 'block'

    document.getElementById('id-instrumento-recebimento').value = idsEnvio; // Transformando a lista em string
    document.getElementById('formRecebimento').reset();

    const modal = new bootstrap.Modal(document.getElementById('modal-recebimento'));
    modal.show();
}


function analisarCalibracao(idEnvio,tag,pontoCalibracao) {

    document.getElementById('modal-title-analise').textContent = `Analisar: ${tag}`;
    document.getElementById('id-instrumento-analise').value = idEnvio;
    document.getElementById('formAnalise').reset();

    document.getElementById('select2-responsavelAnalise-container').textContent = "-------";


    buscarInfoInstrumento(idEnvio,pontoCalibracao)

}

function ultimaAnalise(idEnvio,tag,pontoCalibracao, pdf) {

    const modalTitle = document.getElementById('modal-title-ultima-analise');
    const modal = document.getElementById('modal-ultima-analise');
    modalTitle.textContent = `Analisar: ${tag}`;
    modal.setAttribute('data-id', idEnvio);
    document.getElementById('formUltimaAnalise').reset();

    console.log(idEnvio)
    console.log(pontoCalibracao)

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

        const button = document.getElementById('submit-enviar-instrumento');
        const spinner = document.getElementById('spinner-enviar-instrumento');

        button.disabled = true;
        spinner.style.display = 'block';
        
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
    
                $('#instrumentos-table').DataTable().ajax.reload(null, false); // Reatualiza a tabela

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
        } finally {
            button.disabled = false;
            spinner.style.display = 'none';
        }
    });

    // Captura o evento de envio do formulário
    formRecebimento.addEventListener('submit', async (event) => {
        event.preventDefault(); // Impede o envio padrão do formulário

        const button = document.getElementById('submit-receber-instrumento');
        const spinner = document.getElementById('spinner-receber-instrumento');

        button.disabled = true;
        spinner.style.display = 'block';

        // Cria o objeto com os dados do formulário
        const formData = new FormData(formRecebimento);

        // Converte os dados do formulário para JSON
        const jsonData = {};
        formData.forEach((value, key) => {
            jsonData[key] = value;
        });

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

                $('#instrumentos-table').DataTable().ajax.reload(null, false); // Reatualiza a tabela

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
        } finally {
            button.disabled = false;
            spinner.style.display = 'none';
        }
    });

    // Captura o evento de envio do formulário
    formAnalise.addEventListener('submit', async (event) => {
        event.preventDefault(); // Impede o envio padrão do formulário

        const button = document.getElementById('submit-analisar-instrumento');
        const spinner = document.getElementById('spinner-analisar-instrumento');

        button.disabled = true;
        spinner.style.display = 'block';

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

                $('#instrumentos-table').DataTable().ajax.reload(null, false); // Reatualiza a tabela

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
        } finally {
            button.disabled = false;
            spinner.style.display = 'none';    
        }
    });

    formStatusInstrumento.addEventListener('submit', async (event) => {
        event.preventDefault(); // Impede o envio padrão do formulário
         // Cria o objeto com os dados do formulário
         const formData = new FormData(formStatusInstrumento);

         const button = document.getElementById('submit-substituicao-instrumento');
         const spinner = document.getElementById('spinner-substituicao-instrumento');
 
         button.disabled = true;
         spinner.style.display = 'block';

         // Converte os dados do formulário para JSON
         const jsonData = {};
         formData.forEach((value, key) => {
             jsonData[key] = value;
         });

         let instrumento_substituido = document.getElementById('instrumento-status-substituicao').value

         jsonData['instrumento_substituira'] = instrumento_substituido
 
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
 
                 $('#instrumentos-table').DataTable().ajax.reload(null, false); // Reatualiza a tabela
 
                 // Fecha o modal
                 const modal = bootstrap.Modal.getInstance(document.getElementById('statusInstrumentoModal'));
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
         } finally {
            button.disabled = false;
            spinner.style.display = 'none';
         }
    })
});

// Função para obter o CSRF Token do cookie
function getCsrfToken() {
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) {
        return csrfInput.value;
    }

    // Se não encontrar o input, tenta pegar dos cookies
    const cookieValue = document.cookie
        .split('; ')
        .find((row) => row.startsWith('csrftoken='))
        ?.split('=')[1];

    return cookieValue || '';
}

function buscarInfoInstrumento(idEnvio, pontoCalibracao) {
    Swal.fire({
        title: 'Carregando...',
        text: 'Buscando informações do instrumento...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    fetch(`/instrumento/info/${pontoCalibracao}/${idEnvio}/`)
        .then(response => response.json())
        .then(data => {
            Swal.close()
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
    Swal.fire({
        title: 'Carregando...',
        text: 'Buscando última análise do instrumento...',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    fetch(`/instrumento/info/ultima_analise/${pontoCalibracao}/${idEnvio}/`)
        .then(response => response.json())
        .then(data => {

            Swal.close();
            const info = data.info[0];
            const analise = info.analise_certificado;


            // Preenchendo os campos do modal
            document.getElementById('id-instrumento-ultima-analise').value = pontoCalibracao; // Ou outro identificador relevante
            document.getElementById('incertezaUltimaAnalise').value = analise.incerteza;
            document.getElementById('tendeciaUltimaAnalise').value = analise.tendencia;
            document.getElementById('dataUltimaAnalise').value = analise.data_analise;
            document.getElementById('resultadoUltimaAnalise').value = analise.analise_certificado; // Supondo que este valor seja "aprovado" ou "reprovado"
            document.getElementById('certificadoAtualUltimaAnalise').href = info.pdf;

            // Preenchendo as informações do instrumento
            document.getElementById('faixaNominalUltimaAnalise').textContent = info.ponto_calibracao.faixa_nominal;
            document.getElementById('unidadeUltimaAnalise').value = info.ponto_calibracao.unidade;
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

    document.getElementById('nome-responsavel').value = "";
    document.getElementById('select2-nome-responsavel-container').title = "-------";
    document.getElementById('select2-nome-responsavel-container').textContent = "-------";

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