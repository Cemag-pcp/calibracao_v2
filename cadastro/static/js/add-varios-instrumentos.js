document.addEventListener('DOMContentLoaded', function() {
    const addButton = document.getElementById('addButton');
    const removeButton = document.getElementById('removeButton');

    addButton.addEventListener('click', function() {
        // Clone the element
        const originalElement = document.querySelector('.designar-varios-instrumentos');
        const clone = originalElement.cloneNode(true);
        
        // Clear the values in the cloned selects
        const selects = clone.querySelectorAll('select');
        selects.forEach(select => {
            // Repopula opções copiando do select original correspondente (se existir)
            const originalSelect = originalElement.querySelector(`select.${select.classList[1]}`) || originalElement.querySelector('select');
            if (originalSelect) select.innerHTML = originalSelect.innerHTML;
            select.value = '';
            // Garante classe select2
            if (!select.classList.contains('select2')) {
                select.classList.add('select2');
            }
        });

        // Remove possíveis containers clonado do Select2
        const clonedContainers = clone.querySelectorAll('.select2-container');
        clonedContainers.forEach(c => c.remove());

        // Insert the clone before the add/remove buttons
        const container = document.getElementById('add_remove_cause');
        container.parentNode.insertBefore(clone, container);

        // Inicializa Select2 nos selects clonados
        $(clone).find('select.select2').each(function() {
            $(this).select2({
                dropdownParent: $('#modalDesignarMaisDeUmInstrumento'),
                width: '100%'
            });
        });

        // Enable the remove button
        removeButton.disabled = false;
    });

    removeButton.addEventListener('click', function() {
        const elements = document.querySelectorAll('.designar-varios-instrumentos');
        if (elements.length > 1) {
            // Remove the last cloned element
            elements[elements.length - 1].remove();
        }

        // Disable the remove button if there's only one element left
        if (elements.length <= 2) {
            removeButton.disabled = true;
        }
    });
});
