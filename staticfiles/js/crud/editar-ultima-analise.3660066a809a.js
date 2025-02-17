document.addEventListener("DOMContentLoaded", function() {
    const formUltimaAnalise = document.getElementById("formUltimaAnalise");
    const button = document.getElementById("submit-ultima-analise");
    const spinner = document.getElementById("spinner-ultima-analise");

    formUltimaAnalise.addEventListener("submit", function(event) {
        event.preventDefault()

        button.disabled = true;
        spinner.style.display = 'block';

        const jsonData = {};

        const formData = new FormData(formUltimaAnalise);

        formData.forEach((value, key) => {
            jsonData[key] = value;
        });

        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

        if (!csrfToken) {
            console.error("CSRF Token não encontrado!");
            button.disabled = false;
            spinner.style.display = "none";
            return;
        }

        fetch("/editar-ultima-analise/", {
            method:"POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfToken,
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
                title: `Última análise foi editada com sucesso!`
              });
              $('#instrumentos-table').DataTable().ajax.reload(null, false); // Reatualiza a tabela
              const modalElement = document.getElementById('modal-ultima-analise');
              const modal = bootstrap.Modal.getInstance(modalElement);
              modal.hide();
              
              button.disabled = false;
              spinner.style.display = 'none';

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