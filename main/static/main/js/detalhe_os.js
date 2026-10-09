// static/js/meus_itens.js

function filtrarMeusItens(nomeUsuario) {
    if (!nomeUsuario) return;

    // Procura se já existe um botão de filtro (pílula) para este responsável na barra lateral
    const btnResponsavel = document.querySelector(`button[data-filter-type="responsavel"][data-value="${nomeUsuario}"]`);

    if (btnResponsavel) {
        // Se a pílula existe, alterna o estado ativo dela
        btnResponsavel.classList.toggle('active');
    } else {
        // Se a pílula não estiver visível, manipula diretamente via parâmetros da URL
        const urlParams = new URLSearchParams(window.location.search);
        
        if (urlParams.getAll('responsavel').includes(nomeUsuario)) {
            const responsaveisAtuais = urlParams.getAll('responsavel').filter(r => r !== nomeUsuario);
            urlParams.delete('responsavel');
            responsaveisAtuais.forEach(r => urlParams.append('responsavel', r));
        } else {
            urlParams.append('responsavel', nomeUsuario);
        }

        window.location.search = urlParams.toString();
        return;
    }

    // Atualiza os campos hidden e submete o formulário principal
    if (typeof atualizarCamposHidden === 'function') {
        atualizarCamposHidden();
    }
    if (typeof salvarFiltrosAtuaisNoSessionStorage === 'function') {
        salvarFiltrosAtuaisNoSessionStorage();
    }
    
    const form = document.getElementById('filterForm');
    if (form) {
        form.submit();
    }
}