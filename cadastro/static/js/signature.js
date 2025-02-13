document.addEventListener('DOMContentLoaded', function () {
    // Configuração para o primeiro formulário
    const formResponsavel = document.getElementById('formResponsavel');
    var canvas = document.getElementById('signature-canvas');
    var signaturePad = new SignaturePad(canvas);

    // Configuração para o segundo formulário
    const formEditarResponsavel = document.getElementById('form-editar-responsavel');
    var canvasEdicao = document.getElementById('signature-canvas-edicao');
    var signaturePadEdicao = new SignaturePad(canvasEdicao);

    const formDesignarInstrumentos = document.getElementById('form-designar-varios-instrumentos');
    var canvasDesignarVariosInstrumentos = document.getElementById('signature-canvas-designar-varios-instrumentos');
    var signatureDesignarVariosInstrumentos = new SignaturePad(canvasDesignarVariosInstrumentos);

    // Redimensiona o canvas para o tamanho adequado
    function resizeCanvas(canvas, signaturePad) {
        var ratio = Math.max(window.devicePixelRatio || 1, 1);
        canvas.width = canvas.offsetWidth * ratio;
        canvas.height = canvas.offsetHeight * ratio;
        canvas.getContext('2d').scale(ratio, ratio);
        signaturePad.clear(); // Limpa a assinatura existente
    }

    $('#modal-responsavel').on('shown.bs.modal', function () {
        resizeCanvas(canvas, signaturePad);
    });

    $('#modal-alterar-responsavel').on('shown.bs.modal', function () {
        resizeCanvas(canvasEdicao, signaturePadEdicao);
    });

    $('#modalDesignarMaisDeUmInstrumento').on('shown.bs.modal', function () {
        resizeCanvas(canvasDesignarVariosInstrumentos, signatureDesignarVariosInstrumentos);
    });

    // Capturar o envio do primeiro formulário
    formResponsavel.addEventListener('submit', async (event) => {
        event.preventDefault();
        await enviarFormularioComAssinatura(formResponsavel, signaturePad, '/escolher-responsavel/', 'submit-atribuir-instrumento-responsavel', 'spinner-atribuir-instrumento-responsavel');
    });

    // Capturar o envio do segundo formulário
    formEditarResponsavel.addEventListener('submit', async (event) => {
        event.preventDefault();
    
        const nomeResponsavel = document.getElementById('nome-editar-responsavel').value;
    
        if (!nomeResponsavel) {
            // Se o campo 'nome-editar-responsavel' estiver vazio, ignore a verificação da assinatura
            await enviarFormularioSemAssinatura(formEditarResponsavel, '/editar-responsavel/', 'submit-alterar-instrumento-responsavel', 'spinner-alterar-instrumento-responsavel');
        } else {
            // Se o campo 'nome-editar-responsavel' não estiver vazio, verificar a assinatura
            await enviarFormularioComAssinatura(formEditarResponsavel, signaturePadEdicao, '/editar-responsavel/', 'submit-alterar-instrumento-responsavel', 'spinner-alterar-instrumento-responsavel');
        }
    });

    formDesignarInstrumentos.addEventListener('submit', async (event) => {
        event.preventDefault();
        await enviarFormularioComAssinatura(formDesignarInstrumentos, signatureDesignarVariosInstrumentos, '/designar-mais-instrumentos/', 'submit-designar-mais-instrumento-responsavel', 'spinner-designar-mais-instrumento-responsavel');
    });

    // Função para enviar o formulário com a assinatura
    async function enviarFormularioComAssinatura(form, signaturePad, url, idButton, idSpinner) {
        
        const button = document.getElementById(idButton);
        const spinner = document.getElementById(idSpinner);

        console.log(button)
        button.disabled = true;
        spinner.style.display = 'block';

        const formData = new FormData(form);
        const jsonData = {};
        formData.forEach((value, key) => {
            jsonData[key] = value;
        });

        if (signaturePad.isEmpty()) {
            alert("Por favor, forneça a assinatura.");
            button.disabled = false;
            spinner.style.display = 'none';
            return;
        }

        if (url === '/designar-mais-instrumentos/') {
            const instrumentosSelecionados = [];
            document.querySelectorAll('.instrumento-designado').forEach(select => {
                if (select.value) {
                    instrumentosSelecionados.push(select.value);
                }
            });

            if (instrumentosSelecionados.length === 0) {
                alert("Por favor, selecione pelo menos um instrumento.");
                button.disabled = false;
                spinner.style.display = 'none';
                return;
            }

            jsonData['instrumentos'] = instrumentosSelecionados;  // Adiciona os instrumentos ao JSON
        }

        jsonData['signature'] = signaturePad.toDataURL();

        console.log(jsonData)
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify(jsonData),
            });

            if (response.ok) {
                const data = await response.json();
                Swal.fire({
                    icon: 'success',
                    title: 'Sucesso!',
                    text: data.message || 'Operação concluída com sucesso!',
                });
                $('#instrumentos-table').DataTable().ajax.reload(null, false);
                const modal = bootstrap.Modal.getInstance(document.getElementById(form.id).closest('.modal'));
                modal.hide();
            } else {
                const errorData = await response.json();
                Swal.fire({
                    icon: 'error',
                    title: 'Erro!',
                    text: errorData.message || 'Algo deu errado, tente novamente.',
                });
            }

        } catch (error) {
            console.error('Erro na requisição:', error);
            Swal.fire({
                icon: 'error',
                title: 'Erro de Conexão',
                text: 'Erro ao enviar o formulário. Verifique sua conexão e tente novamente.',
            });
        } finally {
            // Garante que o botão e o spinner sejam redefinidos, independentemente do resultado
            button.disabled = false;
            spinner.style.display = 'none'; // Corrigido para 'style.display'
        }
    }

    async function enviarFormularioSemAssinatura(form, url, idButton, spinnerButton) {

        const button = document.getElementById(idButton);
        const spinner = document.getElementById(spinnerButton);

        button.disabled = true;
        spinner.style.display = 'block';

        const formData = new FormData(form);
        const jsonData = {};
        formData.forEach((value, key) => {
            jsonData[key] = value;
        });
    
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify(jsonData),
            });
    
            if (response.ok) {
                const data = await response.json();
                Swal.fire({
                    icon: 'success',
                    title: 'Sucesso!',
                    text: data.message || 'Operação concluída com sucesso!',
                });
                $('#instrumentos-table').DataTable().ajax.reload(null, false);
                const modal = bootstrap.Modal.getInstance(document.getElementById(form.id).closest('.modal'));
                modal.hide();
            } else {
                const errorData = await response.json();
                Swal.fire({
                    icon: 'error',
                    title: 'Erro!',
                    text: errorData.message || 'Algo deu errado, tente novamente.',
                });
            }
    
        } catch (error) {
            console.error('Erro na requisição:', error);
            Swal.fire({
                icon: 'error',
                title: 'Erro de Conexão',
                text: 'Erro ao enviar o formulário. Verifique sua conexão e tente novamente.',
            });
        } finally {
            // Garante que o botão e o spinner sejam redefinidos, independentemente do resultado
            button.disabled = false;
            spinner.style.display = 'none'; // Corrigido para 'style.display'
        }
    }

    document.getElementById('clear-signature').addEventListener('click', function () {
        signaturePad.clear();
    });

    // Adicionar botão para limpar assinatura no segundo formulário, se necessário
    document.getElementById('clear-signature-edicao').addEventListener('click', function () {
        signaturePadEdicao.clear();
    });

    document.getElementById('clear-signature-add-instrumentos').addEventListener('click', function () {
        signatureDesignarVariosInstrumentos.clear();
    });
});
