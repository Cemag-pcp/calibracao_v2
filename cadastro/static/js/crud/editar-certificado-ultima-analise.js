document.getElementById('editCertificadoAtualUltimaAnalise').addEventListener('click', function() {
    const certificadoAtualUltimaAnalise = document.getElementById('certificadoAtualUltimaAnalise');
    const linkAtual = certificadoAtualUltimaAnalise.href;
    const inputCertificadoAtualUltimaAnalise = document.getElementById('inputCertificadoAtualUltimaAnalise');
    
    inputCertificadoAtualUltimaAnalise.value = linkAtual;
    inputCertificadoAtualUltimaAnalise.style.display = 'block';
    certificadoAtualUltimaAnalise.style.display = 'none';
    this.style.display = 'none';
    document.getElementById('actionButtonsUltimaAnalise').style.display = 'flex';
});

document.getElementById('cancelEditUltimaAnalise').addEventListener('click', function() {
    const certificadoAtualUltimaAnalise = document.getElementById('certificadoAtualUltimaAnalise');
    const inputCertificadoAtualUltimaAnalise = document.getElementById('inputCertificadoAtualUltimaAnalise');
    
    inputCertificadoAtualUltimaAnalise.style.display = 'none';
    certificadoAtualUltimaAnalise.style.display = 'inline';
    document.getElementById('editCertificadoAtualUltimaAnalise').style.display = 'inline';
    document.getElementById('actionButtonsUltimaAnalise').style.display = 'none';
});

document.getElementById('confirmEditUltimaAnalise').addEventListener('click', function() {
    const certificadoAtualUltimaAnalise = document.getElementById('certificadoAtualUltimaAnalise');
    const inputCertificadoAtualUltimaAnalise = document.getElementById('inputCertificadoAtualUltimaAnalise');
    let novoLink = inputCertificadoAtualUltimaAnalise.value.trim();
    
    // Se o campo estiver vazio, remove o certificado
    if (!novoLink) {
        certificadoAtualUltimaAnalise.removeAttribute('href');
        certificadoAtualUltimaAnalise.textContent = 'Nenhum certificado disponível';
        certificadoAtualUltimaAnalise.style.cursor = 'default';
        certificadoAtualUltimaAnalise.onclick = function(e) { e.preventDefault(); };
    } else {
        // Atualiza o link
        certificadoAtualUltimaAnalise.href = novoLink;
        certificadoAtualUltimaAnalise.textContent = 'Visualizar Certificado';
        certificadoAtualUltimaAnalise.style.cursor = 'pointer';
        certificadoAtualUltimaAnalise.onclick = null;
    }
    
    // Esconde o input e mostra o link novamente
    inputCertificadoAtualUltimaAnalise.style.display = 'none';
    certificadoAtualUltimaAnalise.style.display = 'inline';
    document.getElementById('editCertificadoAtualUltimaAnalise').style.display = 'inline';
    document.getElementById('actionButtonsUltimaAnalise').style.display = 'none';
    
    // Aqui você faria a requisição para atualizar no servidor
    atualizarCertificadoUltimaAnaliseNoServidor(novoLink || null);
});

function atualizarCertificadoUltimaAnaliseNoServidor(novoLink) {
    // Substitua esta função pela sua lógica de requisição AJAX
    console.log('Enviando novo certificado da última análise para o servidor:', novoLink);
    const idInstrumento = document.getElementById("modal-ultima-analise").getAttribute('data-id');

    const Toast = Swal.mixin({
        toast: true,
        position: "bottom-end",
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true,
        didOpen: (toast) => {
            toast.onmouseenter = Swal.stopTimer;
            toast.onmouseleave = Swal.resumeTimer;
        }
    });

    // Exemplo com fetch:
    fetch(`/editar-certificado/${idInstrumento}/`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('input[name="csrfmiddlewaretoken"]').value
        },
        body: JSON.stringify({
            certificado: novoLink
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Toast.fire({
                icon: "success",
                title: `Certificado da última análise editado com sucesso!`
            });
        } else {
            Toast.fire({
                icon: "error",
                title: `Erro ao editar o certificado da última análise`
            });
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Ocorreu um erro ao tentar atualizar o certificado da última análise.');
    });
}