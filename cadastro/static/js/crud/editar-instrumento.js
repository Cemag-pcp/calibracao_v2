
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

            document.getElementById("modalEditarLabel").textContent = `Instrumento - ${instrumento.tag}`
            // Preenchendo o modal
            document.getElementById("modal-edit-id").value = instrumento.id;
            document.getElementById("modal-edit-tag").value = instrumento.tag;
            document.getElementById("modal-edit-marca").value = instrumento.marca;
            document.getElementById("modal-edit-tempo").value = instrumento.tempo;
            document.getElementById("modal-edit-ultima").value = instrumento.ultima;
            document.getElementById("modal-edit-proxima").value = instrumento.proxima;
            document.getElementById("modal-edit-tipo").value = instrumento.tipo;

            const typeSelect = document.getElementById("modal-edit-tipo");
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

            // Abrindo o modal
        });
    });
});