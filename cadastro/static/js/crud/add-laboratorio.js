document.addEventListener("DOMContentLoaded", () => {
    const botao = document.getElementById("add-novo-laboratorio");
    const spinner = botao.querySelector(".spinner-border");

    botao.addEventListener("click", (event) => {
        botao.disabled = true;  // Desabilita o botão
        spinner.style.display = "inline-block";  // Exibe o spinner
        
        const laboratorioInstrumento = document.getElementById("input-laboratorio-instrumento").value;
        const selectUnidade = document.getElementById("laboratorio");

        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

        if (!csrfToken) {
            console.error("CSRF Token não encontrado!");
            button.disabled = false;
            spinner.style.display = "none";
            return;
        }

        fetch("/add-laboratorio/", {
            method: "POST",
            headers: {
                "Content-type": "application/json",
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ "laboratorio-instrumento": laboratorioInstrumento }),
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.message || "Erro desconhecido na requisição");
                });
            }
            return response.json();
        })
        .then(data => {
            const option = document.createElement("option");
            Object.assign(option, { value: data.laboratorio_id, textContent: laboratorioInstrumento });
            selectUnidade.appendChild(option);

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
                title: `Laboratório ${laboratorioInstrumento} foi adicionado com sucesso!`
              });
        })
        .catch(error => {
            console.error("Erro: " + error.message);
            Swal.fire({
                icon: "error",
                title: error.message
              });
        })
        .finally(() => {
            document.getElementById("input-laboratorio-instrumento").value = "";
            setTimeout(() => {
                botao.disabled = false;  // Habilita o botão
                spinner.style.display = "none";  // Esconde o spinner
              }, 3000)
        });
    });
});
