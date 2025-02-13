document.addEventListener('DOMContentLoaded',function () {
    document.getElementById('button-modal-designarcao').addEventListener('click',function () {
        modalDesignarMaisInstrumento();
    })
})

function modalDesignarMaisInstrumento() {

    // Resetar o formulário original
    document.getElementById('form-designar-varios-instrumentos').reset();
    document.getElementById('select2-funcionario-designar-varios-instrumentos-container').title = "Selecione um funcionário"
    document.getElementById('select2-funcionario-designar-varios-instrumentos-container').textContent = "Selecione um funcionário"

    // Antes de abrir o modal, limpar todos os clones, mantendo apenas o original
    const existingElements = document.querySelectorAll('.designar-varios-instrumentos');
    if (existingElements.length > 1) {
        // Remove todos, mas deixa o primeiro
        for (let i = 1; i < existingElements.length; i++) {
            existingElements[i].remove();
        }
    }

    fetch('/designar-mais-instrumentos/', { // Substitua pela URL correta
        method: 'GET', // Ou GET, dependendo do seu caso
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json()) // Convertendo resposta para JSON
    .then(data => {
        if (data.sucesso) { 
            var modal = new bootstrap.Modal(document.getElementById('modalDesignarMaisDeUmInstrumento'));
            modal.show(); // Exibe o modal
            console.log(data.instrumentos);

            const selectDesignarInstrumento = document.querySelector(".instrumento-designado");

            if (selectDesignarInstrumento) {
                selectDesignarInstrumento.innerHTML = "<option value=''>Selecione uma opção válida</option>";

                data.instrumentos.forEach(instr => {
                    let option = document.createElement('option');
                    option.value = instr.id;
                    option.textContent = instr.tag;
                    selectDesignarInstrumento.appendChild(option);
                });
            }
        } else {
            alert('Erro ao processar a requisição.');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Ocorreu um erro na requisição.');
    });
}