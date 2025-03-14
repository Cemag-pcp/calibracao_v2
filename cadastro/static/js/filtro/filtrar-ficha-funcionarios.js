// Adiciona os eventos para filtrar as opções
document.addEventListener('DOMContentLoaded',function () {
    const textInputElement = 'filterInput';
    const inputElement = document.getElementById(textInputElement);
    const id_datalist = 'encodings';
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