function processarHistorico(data) {
    // Atribuir os valores retornados do JSON para os elementos da página
    document.getElementById("cabecalho_historico_instrumento").textContent = `Instrumento: ${data.instrumento.tag}` || "Nenhum";
    document.getElementById("responsavel_historico").textContent = data.instrumento.responsavel || "Nenhum";
    document.getElementById("status_equip_historico").textContent = data.instrumento.status_instrumento || "Desconhecido";
    document.getElementById("ult_calib_historico").textContent = data.instrumento.ultima_calibracao || "Não disponível";
    document.getElementById("prox_calib_historico").textContent = data.instrumento.proxima_calibracao || "Não disponível";
    document.getElementById("tipo_equip_historico").textContent = data.instrumento.tipo_equipamento || "Não disponível";
    document.getElementById("tempo_calib_historico").textContent = `${data.instrumento.tempo_calibracao} dias` || "Não disponível";

    const container = document.getElementById("pontos_calibracao_container");
    container.innerHTML = ""; // Limpa os pontos anteriores

    // Verifica se existem pontos de calibração
    if (data.pontos_calibracao.length > 0) {
        data.pontos_calibracao.forEach(ponto => {
            if (ponto.analise_certificado === 'aprovado') {
                statusClass = 'approved';
                statusText = 'Aprovado';
            } else if (ponto.analise_certificado === 'reprovado') {
                statusClass = 'declined';
                statusText = 'Reprovado';
            } else {
                statusClass = 'peding';
                statusText = 'Pendente';
            }

            const pontoHTML = `
                <div class="d-flex justify-content-between align-items-center border p-3 accordion-header">
                    <h6>${ponto.descricao}</h6>
                    <div style="display: flex; gap: 20px; align-items: center;">
                        <strong class="status-${statusClass}" style="font-size: 12px;">
                            ${statusText}
                        </strong>
                    </div>
                </div>
            `;
            container.innerHTML += pontoHTML;
        });
    } else {
        container.innerHTML = `<p>Nenhum ponto de calibração encontrado.</p>`;
    }
}

function processarDataTableHistorico(data) {
    const historicoTableBody = document.querySelector("#historico-table tbody");
    historicoTableBody.innerHTML = "";

    if (data.historico.length > 0) {
        data.historico.forEach(item => {
            const row = `
                <tr>
                    <td>${item.data_mudanca}</td>
                    <td>${item.tipo_mudanca}</td>
                    <td>${item.descricao_mudanca}</td>
                </tr>
            `;
            historicoTableBody.innerHTML += row;
        });
    } else {
        historicoTableBody.innerHTML = `<tr><td colspan="3">Nenhum histórico encontrado.</td></tr>`;
    }
}

document.getElementById('filtrar_instrumento').addEventListener('click', function() {
    let input = document.getElementById('filterInputInstrument');
    let datalist = document.getElementById('instruments-filter').options;
    let selectedId;
    let searchIcon = document.getElementById('searchIcon');
    let spinnerBorder = document.querySelector('.spinner-border');

    this.disabled = true;
    searchIcon.style.display = 'none';
    spinnerBorder.classList.remove('d-none');

    for (let i = 0; i < datalist.length; i++) {
        if (datalist[i].value === input.value) {
            selectedId = datalist[i].getAttribute('data-id');
            break;
        }
    }

    if (selectedId) {
        // Realiza a requisição GET via fetch
        fetch(`/historico/${selectedId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erro HTTP! Status: ${response.status}`);
                }
                return response.json(); // Converte a resposta para JSON
            })
            .then(data => {
                console.log('Dados recebidos:', data);
                searchIcon.style.display = 'block';
                spinnerBorder.classList.add('d-none');
                processarHistorico(data)
            })
            .catch(error => {
                console.error('Erro ao gerar a ficha:', error);
                alert('Erro ao buscar os dados. Tente novamente.');
            })
            .finally(() => {
                this.disabled = false;
                searchIcon.style.display = 'block';
                spinnerBorder.classList.add('d-none');
            });
    } else {
        alert('Instrumento não encontrado. Por favor, selecione uma opção válida.');
        this.disabled = false;
        searchIcon.style.display = 'block';
        spinnerBorder.classList.add('d-none');
    }

    if (selectedId) {
        // Realiza a requisição GET via fetch
        fetch(`/historico/datatable/${selectedId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro HTTP! Status: ${response.status}`);
            }
            return response.json(); // Converte a resposta para JSON
        })
        .then(data => {
            console.log('Dados recebidos do modal histórico:', data);
            processarDataTableHistorico(data)
        })
        .catch(error => {
            console.error('Erro ao gerar a ficha:', error);
            alert('Erro ao buscar os dados. Tente novamente.');
        })
    } 
});