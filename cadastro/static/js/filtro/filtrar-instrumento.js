// Adiciona os eventos para filtrar as opções
document.addEventListener('DOMContentLoaded',function () {
    const textInputElement = 'filterInputInstrument';
    const inputElement = document.getElementById(textInputElement);
    const id_datalist = 'instruments-filter';
    inputElement.addEventListener('input', function() {
        filtrarOpcoes(textInputElement, id_datalist);
    });
    inputElement.addEventListener('click', function() {
        filtrarOpcoes(textInputElement, id_datalist);
    });
    inputElement.addEventListener('focus', function() {
        filtrarOpcoes(textInputElement, id_datalist);
    });
})