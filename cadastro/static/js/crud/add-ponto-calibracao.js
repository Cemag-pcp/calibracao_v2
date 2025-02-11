document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("adicionar-ponto-calibracao");
    const spinner = document.getElementById("spinner-border-adicionar-ponto-calibracao");
    const button = document.getElementById("submit-adicionar-ponto-calibracao");
    form.addEventListener("submit",function (event) {
        event.preventDefault();

        button.disabled = true;
        spinner.style.display = 'block';

        const formData = new FormData(form);
        const jsonData = {};
        formData.forEach((value, key) => {
            jsonData[key] = value
        });

        const cookieValue = document.cookie.split('; ').find((row) => row.startsWith('csrftoken='))?.split('=')[1];
        if (!cookieValue) {
            console.error("CSRF Token não encontrado!");
            button.disabled = false;
            spinner.style.display = 'none';
            return; // Interrompe a requisição se o token não for encontrado
        }

        fetch("/adicionar-ponto-calibracao/", {
            method:"POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": cookieValue
            },
            body: JSON.stringify(jsonData),
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
                title: `Ponto de controle foi adicionado com sucesso!`
              });
        })
        .catch(error => {
            console.error(error);
        })
        .finally(() => {
            setTimeout(() => {
                location.reload()
            }, 2000)
        })
    })
})

document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("modalAdicionarPontoCalibracao");

    modal.addEventListener("show.bs.modal", function (event) {
        const button = event.relatedTarget;

        const instrumentoId = button.getAttribute("data-instrumento-id");

        // Define o valor de instrumento_id_ponto_calibracao no campo hidden do modal
        const instrumentoIdInput = document.getElementById("instrumento_id_ponto_calibracao");
        instrumentoIdInput.value = instrumentoId;

        const unitSelect = document.getElementById("unidade-pc");

        fetch("/adicionar-ponto-calibracao/", {
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
            unitSelect.innerHTML = "";
            const unitList = datas.unitList;
            const optionNodeUnit = document.createElement('option');
            Object.assign(optionNodeUnit, {value:"", selected: true, hidden: true, disabled: true});
            unitSelect.appendChild(optionNodeUnit);
            unitList.forEach(unit => {
                let option = document.createElement("option");
                option.value = unit;
                option.textContent = unit;
                unitSelect.appendChild(option)
            });
            $("#modalAdicionarPontoCalibracao").modal("show");

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
    const botao = document.getElementById("add-nova-unidade");
    const spinner = botao.querySelector(".spinner-border");

    botao.addEventListener("click", (event) => {
        botao.disabled = true;  // Desabilita o botão
        spinner.style.display = "inline-block";  // Exibe o spinner
        
        const unitInstrumento = document.getElementById("input-unidade-instrumento").value;
        const selectUnidade = document.getElementById("unidade-pc");

        const cookieValue = document.cookie.split('; ').find((row) => row.startsWith('csrftoken='))?.split('=')[1];
        if (!cookieValue) {
            console.error("CSRF Token não encontrado!");
            return; // Interrompe a requisição se o token não for encontrado
        }

        fetch("/add-unidade-ponto-calibracao/", {
            method: "POST",
            headers: {
                "Content-type": "application/json",
                'X-CSRFToken': cookieValue
            },
            body: JSON.stringify({ "unidade-instrumento": unitInstrumento }),
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
            Object.assign(option, { value: unitInstrumento, textContent: unitInstrumento });
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
                title: `Unidade ${unitInstrumento} foi adicionado com sucesso!`
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
            document.getElementById("input-unidade-instrumento").value = "";
            setTimeout(() => {
                botao.disabled = false;  // Habilita o botão
                spinner.style.display = "none";  // Esconde o spinner
              }, 3000)
        });
    });
});

