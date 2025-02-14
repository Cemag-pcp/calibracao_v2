function editarPontoCalibracao(id, tag, descricao, status, faixa_nominal, unidade, tolerancia_admissivel) {
    
    document.getElementById('formEditPontoCalibracao').reset();
    
    console.log(id, tag, status, descricao, faixa_nominal, unidade, tolerancia_admissivel)

    const toleranciaFormatada = tolerancia_admissivel != null ? parseInt(tolerancia_admissivel) : "";

    document.getElementById("modal-edit-pc-id").value = id;
    document.getElementById("modal-edit-pc-tag").value = tag;
    document.getElementById("modal-edit-pc-status").value = status;
    document.getElementById("modal-edit-pc-descricao").value = descricao;
    document.getElementById("modal-edit-pc-faixa-nominal").value = faixa_nominal;
    document.getElementById("modal-edit-pc-unidade").value = unidade;
    document.getElementById("modal-edit-pc-tolerancia-admissivel").value = toleranciaFormatada;

    const modal = new bootstrap.Modal(document.getElementById('modalEditPontoCalibracao'));
    modal.show();
}

document.addEventListener("DOMContentLoaded", function() {
    const formEditPontoCalibracao = document.getElementById("formEditPontoCalibracao");
    const button = document.getElementById("submit-edit-pc-instrumento");
    const spinner = document.getElementById("spinner-border-edit-pc-instrumento");

    formEditPontoCalibracao.addEventListener("submit", function(event) {
        event.preventDefault()

        button.disabled = true;
        spinner.style.display = 'block';

        const jsonData = {};

        const formData = new FormData(formEditPontoCalibracao);

        formData.forEach((value, key) => {
            jsonData[key] = value;
        });

        const cookieValue = document.cookie.split('; ').find((row) => row.startsWith('csrftoken='))?.split('=')[1];
        if (!cookieValue) {
            console.error("CSRF Token não encontrado!");
            button.disabled = false;
            spinner.style.display = 'none';
            return; // Interrompe a requisição se o token não for encontrado
        }

        fetch("/editar-ponto-calibracao/", {
            method:"POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": cookieValue,
            },
            body: JSON.stringify(jsonData),
        }).then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.message || "Erro desconhecido na requisição");
                })
            }
            return response.json()

        }).then(data => {
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
              Toast.fire({
                icon: "success",
                title: `Instrumento foi editado com sucesso!`
              });
              setTimeout(() => {
                location.reload();
            }, 1000)
        }).catch(error => {
            console.error(error);
            Swal.fire({
                icon: "error",
                title: error.message
            });
            button.disabled = false;
            spinner.style.display = 'none';
        })
    });
});
