function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

document.addEventListener('DOMContentLoaded', () => {
    const selectBtn = document.getElementById('selectBtn');
    const fileInput = document.getElementById('fileInput');
    const fileNameSpan = document.getElementById('fileName');
    const loadingDiv = document.getElementById('loading');
    const loadingText = document.getElementById('loadingText');
    const resultsSection = document.getElementById('results');
    const propTableBody = document.querySelector('#propTable tbody');
    const saveBtn = document.getElementById('saveBtn');
    const selectorContainer = document.getElementById('selectorContainer');
    const fileSelector = document.getElementById('fileSelector');

    let loadedFilesData = {}; 

    selectBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', async (event) => {
        const files = Array.from(event.target.files);
        if (files.length === 0) return;

        fileNameSpan.textContent = `${files.length} ficheiro(s) selecionado(s).`;
        loadingText.textContent = "A ler propriedades e a analisar o JSON...";
        loadingDiv.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        selectorContainer.classList.add('hidden');

        loadedFilesData = {};
        fileSelector.innerHTML = '';

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await fetch('/sincronizador/api/read-properties/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrftoken },
                    body: formData
                });
                
                const data = await response.json();
                console.log(`Resposta para ${file.name}:`, data); // <-- Permite ver o erro exato no F12 do navegador

                if (response.ok && !data.error) {
                    loadedFilesData[file.name] = {
                        fileObject: file,
                        properties: data.properties,
                        json_data: data.json_data || {}
                    };
                } else {
                    console.error(`Erro retornado para ${file.name}:`, data.error);
                }
            } catch (err) {
                console.error(`Falha de rede ao ler ${file.name}:`, err);
            }
        }

        loadingDiv.classList.add('hidden');
        const fileNames = Object.keys(loadedFilesData);

        if (fileNames.length === 0) {
            alert('Nenhum ficheiro pôde ser lido. Verifique o console (F12) para detalhes do erro.');
            return;
        }

        fileNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            fileSelector.appendChild(option);
        });

        selectorContainer.classList.remove('hidden');
        displayPropertiesForFile(fileNames[0]);
    });

    fileSelector.addEventListener('change', (event) => {
        displayPropertiesForFile(event.target.value);
    });

    function displayPropertiesForFile(filename) {
        const item = loadedFilesData[filename];
        if (!item) return;

        const properties = item.properties;
        const jsonData = item.json_data;

        propTableBody.innerHTML = '';
        
        let cleanJsonData = { ...jsonData };
        if (cleanJsonData.codigo) delete cleanJsonData.codigo;

        const allKeys = new Set([...Object.keys(properties), ...Object.keys(cleanJsonData)]);

        if (allKeys.size === 0) {
            propTableBody.innerHTML = `<tr><td colspan="2" style="text-align: center;">Nenhuma propriedade encontrada.</td></tr>`;
        } else {
            allKeys.forEach(key => {
                const row = document.createElement('tr');
                const tdKey = document.createElement('td');
                tdKey.textContent = key;
                const tdVal = document.createElement('td');
                
                if (key.includes("---") || key === "Massa (kg)" || key === "Volume (m³)" || key === "Área de Superfície (m²)") {
                    tdVal.textContent = properties[key] || "";
                } else {
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.className = 'prop-input';
                    
                    const valFromSW = properties[key] || "";
                    const valFromJson = cleanJsonData[key];
                    input.value = valFromJson !== undefined ? valFromJson : valFromSW;
                    
                    if (valFromJson !== undefined) {
                        input.style.borderLeft = "4px solid #27ae60";
                        input.title = "Preenchido automaticamente via JSON";
                    }

                    input.dataset.key = key; 
                    tdVal.appendChild(input);
                }

                row.appendChild(tdKey);
                row.appendChild(tdVal);
                propTableBody.appendChild(row);
            });
        }
        resultsSection.classList.remove('hidden');
    }

    
    // Guardar propriedades da peça atualmente selecionada
    saveBtn.addEventListener('click', () => {
        const currentFilename = fileSelector.value;
        if (!currentFilename) return;

        const inputs = document.querySelectorAll('.prop-input');
        const updates = {};
        inputs.forEach(input => {
            updates[input.dataset.key] = input.value;
        });

        loadingText.textContent = `A atualizar ${currentFilename} no SolidWorks e a guardar na pasta de rede...`;
        loadingDiv.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        selectorContainer.classList.add('hidden');

        // Envia como JSON puro (Content-Type: application/json), eliminando o FormData e o erro de upload
        fetch('/sincronizador/api/write-properties/', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken 
            },
            body: JSON.stringify({
                filename: currentFilename,
                updates: updates
            })
        })
        .then(response => response.json())
        .then(data => {
            loadingDiv.classList.add('hidden');
            resultsSection.classList.remove('hidden');
            selectorContainer.classList.remove('hidden');
            
            if (data.error) throw new Error(data.error);
            
            alert(`Sucesso! O ficheiro ${currentFilename} foi atualizado e guardado na pasta de rede.`);
        })
        .catch(error => {
            loadingDiv.classList.add('hidden');
            resultsSection.classList.remove('hidden');
            selectorContainer.classList.remove('hidden');
            alert('Falha ao guardar: ' + error.message);
        });
    });
});