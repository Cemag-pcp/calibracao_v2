$(document).ready(function(){
    // Função para habilitar o comportamento de dropdown
    function enableDropdowns() {
        $(".toggle-dropdown").each(function() {
            var toggleButton = $(this);
            var dropdown = toggleButton.next(".custom-dropdown");

            // Exibe ou oculta o dropdown ao clicar no botão
            toggleButton.click(function(event){
                event.stopPropagation();
                dropdown.toggle();
            });

            // Fecha o dropdown se o clique for fora do botão ou do dropdown
            $(document).click(function(event){
                if (!$(event.target).closest(toggleButton.add(dropdown)).length) {
                    dropdown.hide();
                }
            });
        });
    }

    // Habilita os dropdowns automaticamente
    enableDropdowns();
});