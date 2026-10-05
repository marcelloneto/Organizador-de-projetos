(function() {
    // Garante as variáveis globais da OS e do Usuário
    window.OS_ID = window.OS_ID || "";
    window.USER_ID = window.USER_ID || "";

    document.addEventListener("DOMContentLoaded", function() {
        const osId = window.OS_ID;
        const userId = window.USER_ID;

        const storageKeyArvore = `arvore_estado_os_${osId}_user_${userId}`;
        const storageKeyFiltros = `filtros_os_${osId}_user_${userId}`;

        // --- 1. RESTAURAR CAMPO DE PESQUISA DA SESSÃO ---
        const filtrosSalvos = sessionStorage.getItem(storageKeyFiltros);
        const campoBusca = document.getElementById('q');
        
        if (filtrosSalvos && campoBusca && !campoBusca.value) {
            try {
                const dados = JSON.parse(filtrosSalvos);
                if (dados.q) {
                    campoBusca.value = dados.q;
                }
            } catch (e) {
                console.error("Erro ao carregar termo de busca", e);
            }
        }

        if (campoBusca) {
            campoBusca.addEventListener('input', function() {
                const filtrosData = { q: campoBusca.value };
                sessionStorage.setItem(storageKeyFiltros, JSON.stringify(filtrosData));
            });
        }

        // --- 2. RESTAURAR ESTADO DA ÁRVORE DA SESSÃO ---
        const estadoSalvo = sessionStorage.getItem(storageKeyArvore);
        if (estadoSalvo) {
            try {
                const indicesAbertos = JSON.parse(estadoSalvo);
                const elementosDetails = document.querySelectorAll("details");
                
                elementosDetails.forEach((detalhe, index) => {
                    if (indicesAbertos.includes(index)) {
                        detalhe.setAttribute("open", "true");
                    } else {
                        detalhe.removeAttribute("open");
                    }
                });
            } catch (e) {
                console.error("Erro ao carregar estado da árvore", e);
            }
        } else {
            expandirTodos(false);
        }

        // --- 3. SALVAR ESTADO DA ÁRVORE SEMPRE QUE MUDAR ---
        document.querySelectorAll("details").forEach((detalhe) => {
            detalhe.addEventListener("toggle", function() {
                const elementosDetails = document.querySelectorAll("details");
                const indicesAbertos = [];
                
                elementosDetails.forEach((el, idx) => {
                    if (el.hasAttribute("open")) {
                        indicesAbertos.push(idx);
                    }
                });
                
                sessionStorage.setItem(storageKeyArvore, JSON.stringify(indicesAbertos));
            });
        });

        // --- 4. ATUALIZAÇÃO AUTOMÁTICA A CADA 15 SEGUNDOS ---
        setInterval(function() {
            window.location.reload();
        }, 15000);
    });

    // --- FUNÇÕES EXPOSTAS GLOBALMENTE PARA O HTML ---
    window.toggleFilter = function(tipo, valor) {
        const btn = document.querySelector(`button[data-filter-type="${tipo}"][data-value="${valor}"]`);
        if (btn) {
            btn.classList.toggle('active');
            atualizarCamposHidden();
            
            const form = document.getElementById('filterForm');
            if (form) {
                form.submit();
            }
        } else {
            console.error("Botão de filtro não encontrado:", tipo, valor);
        }
    };

    function atualizarCamposHidden() {
        const container = document.getElementById('selectedHiddenContainer');
        if (!container) return;
        
        container.innerHTML = '';
        const botoesAtivos = document.querySelectorAll('.filter-pill.active');
        
        botoesAtivos.forEach(btn => {
            document.createElement('input');
            const tipo = btn.getAttribute('data-filter-type');
            const valor = btn.getAttribute('data-value');
            
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = tipo;
            input.value = valor;
            container.appendChild(input);
        });
    }

    window.expandirTodos = function(abrir) {
        const elementosDetails = document.querySelectorAll("details");
        elementosDetails.forEach(function(detalhe) {
            if (abrir) {
                detalhe.setAttribute("open", "true");
            } else {
                detalhe.removeAttribute("open");
            }
        });

        const osId = window.OS_ID;
        const userId = window.USER_ID;
        const storageKeyArvore = `arvore_estado_os_${osId}_user_${userId}`;

        const indicesAbertos = [];
        if (abrir) {
            elementosDetails.forEach((el, idx) => indicesAbertos.push(idx));
        }
        sessionStorage.setItem(storageKeyArvore, JSON.stringify(indicesAbertos));
    };
})();