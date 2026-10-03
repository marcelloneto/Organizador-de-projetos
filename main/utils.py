import os
import shutil
from datetime import datetime

# Caminho raiz base definido no seu projeto
CAMINHO_BASE_PROJETOS = r"C:\Users\marce\OneDrive\Marcello Neto\Marcello - Engenharia\Projetos pessoais\PROJETOS"

def criar_pasta_se_nao_existir(caminho):
    """Cria a pasta no Windows Explorer se ela não existir."""
    if caminho and not os.path.exists(caminho):
        os.makedirs(caminho, exist_ok=True)
    return caminho

def obter_caminho_os(numero_os, descricao_os):
    """Retorna e cria o caminho da OS: OS-Número da OS - Descrição da OS"""
    nome_pasta = f"OS-{numero_os} - {descricao_os}".upper()
    caminho = os.path.join(CAMINHO_BASE_PROJETOS, nome_pasta)
    return criar_pasta_se_nao_existir(caminho)

def obter_caminho_conjunto(caminho_os, numero_conjunto, nome_conjunto):
    """Retorna e cria o caminho do Conjunto: Número do conjunto - Nome do Conjunto"""
    nome_pasta = f"{numero_conjunto} - {nome_conjunto}".upper()
    caminho = os.path.join(caminho_os, nome_pasta)
    return criar_pasta_se_nao_existir(caminho)

def obter_caminho_tipo_documento(caminho_conjunto, acronimo_tipo, nome_tipo):
    """Retorna e cria o caminho do Tipo de Documento: Acrônimo - Nome do tipo de documento"""
    nome_pasta = f"{acronimo_tipo} - {nome_tipo}".upper()
    caminho = os.path.join(caminho_conjunto, nome_pasta)
    return criar_pasta_se_nao_existir(caminho)

def obter_caminho_subconjunto(caminho_tipo_doc, numero_subconjunto, nome_subconjunto=None):
    """
    Retorna e cria o caminho do Subconjunto.
    Se o título do subconjunto estiver em branco, NÃO cria pasta e retorna o caminho anterior.
    """
    if not nome_subconjunto or not str(nome_subconjunto).strip():
        return caminho_tipo_doc # Pula a etapa se estiver em branco
    
    nome_pasta = f"{numero_subconjunto} - {nome_subconjunto}".upper()
    caminho = os.path.join(caminho_tipo_doc, nome_pasta)
    return criar_pasta_se_nao_existir(caminho)

def gerenciar_upload_arquivo_explorer(pasta_destino, arquivo_origem_path, codigo_revisao_esperado):
    """
    Gerencia o upload/cópia do arquivo para a pasta do Explorer:
    - Valida o nome do arquivo (Código-Revisão).
    - Se já existir arquivo idêntico, move o anterior para a pasta OBSOLETO com data e horário (sem segundos).
    - Se for salvamento em branco (sem novo arquivo), verifica se o arquivo físico ainda existe na pasta.
    """
    if not arquivo_origem_path:
        # Salvamento em branco: verifica se o arquivo esperado ainda existe no Explorer
        extensoes_possibles = ['.docx', '.doc', '.pdf', '.xlsx', '.xls', '.slddrw', '.idw', '.dwg', '.dxf']
        for ext in extensoes_possibles:
            caminho_potencial = os.path.join(pasta_destino, f"{codigo_revisao_esperado}{ext}")
            if os.path.exists(caminho_potencial):
                return caminho_potencial # Mantém o arquivo existente
        return None # Nenhum arquivo encontrado, pode limpar

    # Extrai informações do arquivo de origem
    nome_arquivo_completo = os.path.basename(arquivo_origem_path)
    nome_base, ext = os.path.splitext(nome_arquivo_completo)
    ext = ext.lower()

    # Validação rigorosa do nome do arquivo no Explorer
    if nome_base.upper() != codigo_revisao_esperado.upper():
        raise ValueError(f"O nome do arquivo ('{nome_arquivo_completo}') não confere com o padrão obrigatório: '{codigo_revisao_esperado}{ext}'")

    # Garante que a pasta de destino final existe no Explorer
    criar_pasta_se_nao_existir(pasta_destino)
    caminho_destino_final = os.path.join(pasta_destino, f"{codigo_revisao_esperado}{ext}")

    # Se já existir um arquivo com o mesmo nome exato, move para OBSOLETO com Data e Horário (sem segundos)
    if os.path.exists(caminho_destino_final):
        pasta_obsoleto = os.path.join(pasta_destino, "OBSOLETO")
        criar_pasta_se_nao_existir(pasta_obsoleto)

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        nome_arq, extensao = os.path.splitext(os.path.basename(caminho_destino_final))
        novo_nome_obsoleto = f"{nome_arq}_{timestamp}{extensao}"
        caminho_obsoleto_final = os.path.join(pasta_obsoleto, novo_nome_obsoleto)

        shutil.move(caminho_destino_final, caminho_obsoleto_final)

    # Copia o novo arquivo para a pasta do Explorer
    shutil.copy2(arquivo_origem_path, caminho_destino_final)
    return caminho_destino_final

def executar_backup_e_exclusao_pasta(caminho_pasta_alvo):
    """
    Ao excluir qualquer item (Conjunto, Subconjunto, etc.):
    - Cria uma pasta de backup na pasta imediatamente acima.
    - Nomeia o backup como: [NomeDaPastaOriginal]_[DD-MM-AAAA_HH-MM] (sem segundos).
    - Copia todo o conteúdo da pasta original para o backup.
    - Exclui a pasta original do Explorer em sequência.
    """
    if caminho_pasta_alvo and os.path.exists(caminho_pasta_alvo):
        diretorio_pai = os.path.dirname(caminho_pasta_alvo)
        nome_pasta_original = os.path.basename(caminho_pasta_alvo)
        
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        nome_pasta_backup = f"{nome_pasta_original}_{timestamp}"
        caminho_backup = os.path.join(diretorio_pai, nome_pasta_backup)
        
        # Cria a pasta de backup, copia a árvore inteira e remove a original
        shutil.copytree(caminho_pasta_alvo, caminho_backup)
        shutil.rmtree(caminho_pasta_alvo)
        return caminho_backup
    return None