document.addEventListener('DOMContentLoaded', function() {
    const addButton = document.getElementById('addButton');
    const removeButton = document.getElementById('removeButton');

    addButton.addEventListener('click', function() {
        // Clone the element
        const originalElement = document.querySelector('.designar-varios-instrumentos');
        const clone = originalElement.cloneNode(true);
        
        // Clear the values in the cloned selects
        const selects = clone.querySelectorAll('select');
        selects.forEach(select => select.value = '');

        // Insert the clone before the add/remove buttons
        const container = document.getElementById('add_remove_cause');
        container.parentNode.insertBefore(clone, container);

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