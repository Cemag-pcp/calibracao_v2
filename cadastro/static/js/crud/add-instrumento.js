document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('buttonAddInstrumento').addEventListener('click', () => {
        
        const typeSelect = document.getElementById("modal-add-tipo");
        const statusSelect = document.getElementById("modal-add-status");

        $("#modalAddInstrumento").modal("show");

        fetch("/add-instrumento/", {
            method: "GET"
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => {
                    throw new Error(err.message || "Erro desconhecido na requisição");
                });
            }
            return response.json();

        }).then(datas => {
            typeSelect.innerHTML = "";
            statusSelect.innerHTML = "";
            const typeList = datas.typeList;
            const optionNodeType = document.createElement('option');
            Object.assign(optionNodeType, {value:"", selected: true, hidden: true, disabled: true});
            typeSelect.appendChild(optionNodeType);
            typeList.forEach(type => {
                let option = document.createElement("option");
                option.value = type;
                option.textContent = type;
                typeSelect.appendChild(option)
            });

            const statusList = datas.statusList;
            const optionNodeStatus = document.createElement('option');
            Object.assign(optionNodeStatus, {value:"", selected: true, hidden: true, disabled: true});
            statusSelect.appendChild(optionNodeStatus);
            statusList.forEach(status => {
                let option = document.createElement("option");
                option.value = status;
                option.textContent = status;
                statusSelect.appendChild(option);
            });
        }).catch(error => {
            console.error("Erro: " + error.message);
            Swal.fire({
                icon: "error",
                title: error.message
              });
        })

    })
})

document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("formAddInstrumento");
    const button = document.getElementById("submit-adicionar-instrumento");
    const spinner = document.getElementById("spinner-border-adicionar-instrumento");

    form.addEventListener("submit", (event) => {
        event.preventDefault();

        button.disabled = true;
        spinner.style.display = "block";
        
        const formData = new FormData(form);

        fetch("/add-instrumento/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCsrfTokenAddInstrument(),
            },
            body: formData,
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
                title: `Instrumento foi adicionado com sucesso!`
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
            setTimeout(() => {
                location.reload();
            }, 1000)
        })
    })
})

document.addEventListener("DOMContentLoaded", () => {
    const botao = document.getElementById("add-novo-tipo");
    const spinner = botao.querySelector(".spinner-border");

    botao.addEventListener("click", (event) => {
        botao.disabled = true;  // Desabilita o botão
        spinner.style.display = "inline-block";  // Exibe o spinner
        
        const tipoInstrumento = document.getElementById("input-tipo-instrumento").value;
        const selectTipo = document.getElementById("modal-add-tipo");

        fetch("/add-tipo-instrumento/", {
            method: "POST",
            headers: {
                "Content-type": "application/json",
                'X-CSRFToken': getCsrfTokenAddInstrument()
            },
            body: JSON.stringify({ "tipo-instrumento": tipoInstrumento }),
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
            Object.assign(option, { value: tipoInstrumento, textContent: tipoInstrumento });
            selectTipo.appendChild(option);

            const Toast = Swal.mixin({
                toast: true,
                position: "top-end",
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
                title: `Instrumento ${tipoInstrumento} foi adicionado com sucesso!`
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
            document.getElementById("input-tipo-instrumento").value = "";
            setTimeout(() => {
                botao.disabled = false;  // Habilita o botão
                spinner.style.display = "none";  // Esconde o spinner
              }, 3000)
        });
    });
});

function getCsrfTokenAddInstrument() {
    const cookieValue = document.cookie
        .split('; ')
        .find((row) => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}