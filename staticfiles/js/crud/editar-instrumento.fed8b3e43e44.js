
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".open-modal").forEach(button => {
        button.addEventListener("click", function() {
            let instrumento = {
                id: this.getAttribute("data-id"),
                tag: this.getAttribute("data-tag"),
                tipo: this.getAttribute("data-tipo"),
                marca: this.getAttribute("data-marca"),
                status: this.getAttribute("data-status"),
                tempo: this.getAttribute("data-tempo"),
                ultima: this.getAttribute("data-ultima"),
                proxima: this.getAttribute("data-proxima")
            };

            $("#modalEditar").modal("show");
            const typeSelect = document.getElementById("modal-edit-tipo");
            const optionLoading = document.createElement("option");
            optionLoading.value = "Carregando...";
            optionLoading.textContent = "Carregando...";
            typeSelect.appendChild(optionLoading)

            document.getElementById("modalEditarLabel").textContent = `Instrumento - ${instrumento.tag}`
            // Preenchendo o modal
            document.getElementById("modal-edit-id").value = instrumento.id;
            document.getElementById("modal-edit-tag").value = instrumento.tag;
            document.getElementById("modal-edit-marca").value = instrumento.marca;
            document.getElementById("modal-edit-tempo").value = instrumento.tempo;
            document.getElementById("modal-edit-ultima").value = instrumento.ultima;
            document.getElementById("modal-edit-proxima").value = instrumento.proxima;
            typeSelect.value = "Carregando...";

            const statusSelect = document.getElementById("modal-edit-status");

            fetch("/add-instrumento/", {
                method: "GET"
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error("Erro na requisição: " + response.status);
                }
                return response.json();

            }).then(datas => {
                typeSelect.innerHTML = "";
                statusSelect.innerHTML = "";
                const typeList = datas.typeList;
                typeList.forEach(type => {
                    let option = document.createElement("option");
                    option.value = type;
                    option.textContent = type;
                    typeSelect.appendChild(option)
                });

                const statusList = datas.statusList;
                statusList.forEach(status => {
                    let option = document.createElement("option");
                    option.value = status;
                    option.textContent = status;
                    statusSelect.appendChild(option);
                });
                typeSelect.value = instrumento.tipo;
                statusSelect.value = instrumento.status;
            }).catch(error => {
                console.error("Erro ", error)
            })
        });
    });
});



document.addEventListener("DOMContentLoaded", function() {
    const formEdit = document.getElementById("form-edit");
    const button = document.getElementById("submit-editar-instrumento");
    const spinner = document.getElementById("spinner-border-editar-instrumento");

    formEdit.addEventListener("submit", function(event) {
        event.preventDefault()

        button.disabled = true;
        spinner.style.display = 'block';

        const jsonData = {};

        const formData = new FormData(formEdit);

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

        fetch("/edit-instrumento/", {
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
                title: `Ponto de Calibração foi editado com sucesso!`
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