document.getElementById('editCertificadoAtual').addEventListener('click', function() {
    const certificadoAtual = document.getElementById('certificadoAtual');
    const linkAtual = certificadoAtual.href;
    const inputCertificadoAtual = document.getElementById('inputCertificadoAtual');
    
    inputCertificadoAtual.value = linkAtual;
    inputCertificadoAtual.style.display = 'block';
    certificadoAtual.style.display = 'none';
    this.style.display = 'none';
    document.getElementById('actionButtons').style.display = 'flex';
});

document.getElementById('cancelEdit').addEventListener('click', function() {
    const certificadoAtual = document.getElementById('certificadoAtual');
    const inputCertificadoAtual = document.getElementById('inputCertificadoAtual');
    
    inputCertificadoAtual.style.display = 'none';
    certificadoAtual.style.display = 'inline';
    document.getElementById('editCertificadoAtual').style.display = 'inline';
    document.getElementById('actionButtons').style.display = 'none';
});

document.getElementById('confirmEdit').addEventListener('click', function() {
    const certificadoAtual = document.getElementById('certificadoAtual');
    const inputCertificadoAtual = document.getElementById('inputCertificadoAtual');
    let novoLink = inputCertificadoAtual.value.trim();
    
    // Se o campo estiver vazio, remove o certificado
    if (!novoLink) {
        certificadoAtual.removeAttribute('href');
        certificadoAtual.textContent = 'Nenhum certificado disponível';
        certificadoAtual.style.cursor = 'default';
        certificadoAtual.onclick = function(e) { e.preventDefault(); };
    } else {
        // Atualiza o link
        certificadoAtual.href = novoLink;
        certificadoAtual.textContent = 'Visualizar Certificado';
        certificadoAtual.style.cursor = 'pointer';
        certificadoAtual.onclick = null;
    }
    
    // Esconde o input e mostra o link novamente
    inputCertificadoAtual.style.display = 'none';
    certificadoAtual.style.display = 'inline';
    document.getElementById('editCertificadoAtual').style.display = 'inline';
    document.getElementById('actionButtons').style.display = 'none';
    
    // Aqui você faria a requisição para atualizar no servidor
    atualizarCertificadoNoServidor(novoLink || null);
});

function atualizarCertificadoNoServidor(novoLink) {
    // Substitua esta função pela sua lógica de requisição AJAX
    console.log('Enviando novo certificado para o servidor:', novoLink);
    const idInstrumento = document.getElementById("id-instrumento-analise").value;

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
                title: `Certificado editado com sucesso!`
            });
        } else {
            Toast.fire({
                icon: "error",
                title: `Erro ao editar o certificado`
            });
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Ocorreu um erro ao tentar atualizar o certificado.');
    });
}