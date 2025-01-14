function filtrarOpcoes() {
    const inputValue = document.getElementById('filterInput').value.toLowerCase();
    const datalist = document.getElementById('encodings');
    const options = Array.from(datalist.querySelectorAll('option'));

    // Filtra as opções que começam com o valor digitado e ordena lexicograficamente
    const opcoesFiltradas = options
      .filter(option => option.value.toLowerCase().startsWith(inputValue))
      .sort((a, b) => a.value.localeCompare(b.value))
      .slice(0, 5); // Pega as 5 primeiras opções filtradas

    // Oculta e desabilita todas as opções inicialmente
    options.forEach(option => {
      option.style.display = 'none';
      option.disabled = true;
    });

    // Exibe e habilita apenas as opções filtradas
    opcoesFiltradas.forEach(option => {
      option.style.display = '';
      option.disabled = false;
    });
  }

  // Adiciona os eventos para filtrar as opções
  const inputElement = document.getElementById('filterInput');
  inputElement.addEventListener('input', filtrarOpcoes);
  inputElement.addEventListener('click', filtrarOpcoes);
  inputElement.addEventListener('focus', filtrarOpcoes);