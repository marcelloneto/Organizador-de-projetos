from django.shortcuts import render, redirect, get_object_or_404
from .models import OrdemServico, Conjunto, Subconjunto, Item, DocumentoItem, EXTENSOES_EDITAVEIS_PERMITIDAS
from .forms import OrdemServicoForm, ConjuntoForm, SubconjuntoForm, ItemForm, DocumentoItemForm, DocumentoArquivosForm
import os
from django.http import Http404, FileResponse
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from django.contrib.auth.decorators import login_required

def lista_os_view(request):
    ordens_servico = OrdemServico.objects.all().order_by('-id')
    return render(request, 'main/lista_os.html', {'ordens_servico': ordens_servico})

def minha_view(request):
    # Verifica se o utilizador está autenticado
    if request.user.is_authenticated:
        usuario_atual = request.user.username
        pagina = request.path
        print(f"O utilizador atual é: {usuario_atual}")
        print(f"utilizando a página: {pagina}")
    else:
        print("Nenhum utilizador logado.")
    

def detalhe_os_view(request, os_id):
    os_obj = get_object_or_404(OrdemServico, id=os_id)
    minha_view(request)
    # 1. Captura múltiplos valores dos filtros da barra lateral
    conjuntos_selecionados_list = request.GET.getlist('conjunto')
    tipos_selecionados_list = request.GET.getlist('tipo_doc')
    responsaveis_selecionados_list = request.GET.getlist('responsavel')
    etapas_selecionadas_list = request.GET.getlist('etapa') # Novo filtro de etapa
    data_entrega_filtro = request.GET.get('data_entrega')
    print(data_entrega_filtro)
    # 2. Captura o termo de busca textual
    termo_busca = request.GET.get('q', '').strip()
    
    # Dados base para popular os filtros da barra lateral
    conjuntos_disponiveis = os_obj.conjuntos.all().order_by('acronimo_vv')
    
    todos_docs = DocumentoItem.objects.filter(item__subconjunto__conjunto__os=os_obj)
    tipos_documento_disponiveis = todos_docs.values_list('tipo_documento', flat=True).distinct().order_by('tipo_documento')
    responsaveis_disponiveis = todos_docs.exclude(responsavel__isnull=True).exclude(responsavel='').values_list('responsavel', flat=True).distinct().order_by('responsavel')
    
    # Extrai etapas disponíveis (utilizando o campo 'status' ou o que definir sua etapa de desenvolvimento)
    etapas_disponiveis = todos_docs.exclude(status__isnull=True).exclude(status='').values_list('status', flat=True).distinct().order_by('status')

    # Filtra os conjuntos caso o usuário tenha selecionado algum
    conjuntos = conjuntos_disponiveis
    if conjuntos_selecionados_list:
        conjuntos = conjuntos.filter(acronimo_vv__in=conjuntos_selecionados_list)

    

    # Estrutura a hierarquia aplicando todos os filtros cruzados
    contexto_hierarquico = []
    for conjunto in conjuntos:
        subconjuntos = conjunto.subconjuntos.all().order_by('acronimo_uu')
        
        subconjuntos_lista = []
        for sub in subconjuntos:
            itens = sub.itens.all().order_by('acronimo_tt')
            
            for item in itens:
                documentos = item.documentos.all()
                
                # Filtros aplicados
                if tipos_selecionados_list:
                    documentos = documentos.filter(tipo_documento__in=tipos_selecionados_list)
                
                if responsaveis_selecionados_list:
                    documentos = documentos.filter(responsavel__in=responsaveis_selecionados_list)
                
                if etapas_selecionadas_list:
                    documentos = documentos.filter(status__in=etapas_selecionadas_list)
                
                if termo_busca:
                    documentos = documentos.filter(
                        Q(tipo_documento__icontains=termo_busca) |
                        Q(revisao__icontains=termo_busca) |
                        Q(item__titulo_3__icontains=termo_busca) |
                        Q(item__subconjunto__titulo_2__icontains=termo_busca) |
                        Q(item__subconjunto__conjunto__titulo_1__icontains=termo_busca)
                    )

                

                if data_entrega_filtro:
                    # Filtra registros cuja data seja menor ou igual à selecionada (tudo anterior ou na mesma data)
                    documentos = documentos.filter(data_emissao_final__lte=data_entrega_filtro)
                
                documentos = documentos.order_by('tipo_documento')
                
                if not (termo_busca or 
                tipos_selecionados_list or 
                responsaveis_selecionados_list or 
                etapas_selecionadas_list or 
                data_entrega_filtro) or documentos.exists():
                    subconjuntos_lista.append({
                        'subconjunto': sub,
                        'item': item,
                        'documentos': documentos
                    })
                
        if subconjuntos_lista:
            contexto_hierarquico.append({
                'conjunto': conjunto,
                'subconjuntos': subconjuntos_lista
            })
    


    return render(request, 'main/detalhe_os.html', {
        'os': os_obj,
        'os_obj': os_obj,
        'conjuntos_disponiveis': conjuntos_disponiveis,
        'conjuntos_selecionados_list': conjuntos_selecionados_list,
        'tipos_documento_disponiveis': tipos_documento_disponiveis,
        'tipos_selecionados_list': tipos_selecionados_list,
        'responsaveis_disponiveis': responsaveis_disponiveis,
        'responsaveis_selecionados_list': responsaveis_selecionados_list,
        'etapas_disponiveis': etapas_disponiveis,
        'etapas_selecionadas_list': etapas_selecionadas_list,
        'data_entrega_selecionada': data_entrega_filtro,
        'contexto_hierarquico': contexto_hierarquico,
        'termo_busca': termo_busca,
    })

def cadastrar_os(request):
    form = OrdemServicoForm(request.POST or None)
    if form.is_valid():
        os_obj = form.save()
        docs_selecionados = form.cleaned_data.get('documentos_iniciais', [])
        if docs_selecionados:
            conjunto_padrao = Conjunto.objects.create(
                os=os_obj, acronimo_vv='01', titulo_1=f"Conjunto Principal - {os_obj.numero_os}", disciplina='MEC', criado_por=os_obj.criado_por
            )
            subconjunto_padrao = Subconjunto.objects.create(
                conjunto=conjunto_padrao, acronimo_uu='01', titulo_2='Subconjunto Principal', criado_por=os_obj.criado_por
            )
            item_padrao = Item.objects.create(
                subconjunto=subconjunto_padrao, acronimo_tt='01', titulo_3='Item Principal', criado_por=os_obj.criado_por
            )
            for tipo in docs_selecionados:
                DocumentoItem.objects.create(
                    item=item_padrao, tipo_documento=tipo, criado_por=os_obj.criado_por
                )
        return redirect('detalhe_os', os_id=os_obj.id)
    return render(request, 'main/form_generico.html', {'form': form, 'titulo': 'Nova Ordem de Serviço'})

def editar_os(request, os_id):
    os_obj = get_object_or_404(OrdemServico, id=os_id)
    form = OrdemServicoForm(request.POST or None, instance=os_obj)
    if 'documentos_iniciais' in form.fields:
        del form.fields['documentos_iniciais']
    if form.is_valid():
        form.save()
        return redirect('detalhe_os', os_id=os_obj.id)
    return render(request, 'main/form_generico.html', {'form': form, 'titulo': f'Editar OS: {os_obj.numero_os}'})

def excluir_os(request, os_id):
    os_obj = get_object_or_404(OrdemServico, id=os_id)
    if request.method == 'POST':
        os_obj.delete()
        return redirect('lista_os')
    return render(request, 'main/confirmar_exclusao.html', {'objeto': os_obj.numero_os, 'tipo': 'Ordem de Serviço'})

# --- CONJUNTO ---
def cadastrar_conjunto(request, os_id):
    os_obj = get_object_or_404(OrdemServico, id=os_id)
    form = ConjuntoForm(request.POST or None, initial={'os': os_obj})
    if form.is_valid():
        conjunto = form.save(commit=False)
        conjunto.os = os_obj  # Associa estritamente à OS da URL
        conjunto.save()
        return redirect('detalhe_os', os_id=os_obj.id)
    return render(request, 'main/form_generico.html', {'form': form, 'titulo': f'Novo Conjunto (OS: {os_obj.numero_os})'})

def editar_conjunto(request, pk):
    conjunto = get_object_or_404(Conjunto, pk=pk)
    form = ConjuntoForm(request.POST or None, instance=conjunto)
    if form.is_valid():
        form.save()
        return redirect('detalhe_os', os_id=conjunto.os.id)
    return render(request, 'main/form_generico.html', {'form': form, 'titulo': f'Editar Conjunto: {conjunto.acronimo_vv}'})

def excluir_conjunto(request, pk):
    conjunto = get_object_or_404(Conjunto, pk=pk)
    os_id = conjunto.os.id
    if request.method == 'POST':
        conjunto.delete() # Ao deletar aqui, o Django executa o método delete() do model que dispara o backup no Explorer automaticamente
        return redirect('detalhe_os', os_id=os_id)
    return render(request, 'main/confirmar_exclusao.html', {'objeto': conjunto.titulo_1, 'tipo': 'Conjunto'})

# --- SUBCONJUNTO ---
def cadastrar_subconjunto(request, conjunto_id):
    conjunto = get_object_or_404(Conjunto, id=conjunto_id)
    
    # Passa o conjunto_pai para o formulário filtrar as opções
    if request.method == 'POST':
        form = SubconjuntoForm(request.POST, conjunto_pai=conjunto)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.conjunto = conjunto
            sub.save()
            return redirect('detalhe_os', os_id=conjunto.os.id)
    else:
        form = SubconjuntoForm(conjunto_pai=conjunto)
        
    return render(request, 'main/form_generico.html', {'form': form, 'titulo': f'Novo Subconjunto (Conjunto: {conjunto.acronimo_vv})'})

def editar_subconjunto(request, pk):
    sub = get_object_or_404(Subconjunto, pk=pk)
    form = SubconjuntoForm(request.POST or None, instance=sub)
    if form.is_valid():
        form.save()
        return redirect('detalhe_os', os_id=sub.conjunto.os.id)
    return render(request, 'main/form_generico.html', {'form': form, 'titulo': f'Editar Subconjunto: {sub.acronimo_uu}'})

def excluir_subconjunto(request, pk):
    sub = get_object_or_404(Subconjunto, pk=pk)
    os_id = sub.conjunto.os.id
    if request.method == 'POST':
        sub.delete()
        
        return redirect('detalhe_os', os_id=os_id)
    return render(request, 'main/confirmar_exclusao.html', {'objeto': sub.titulo_2 or sub.acronimo_uu, 'tipo': 'Subconjunto'})

# --- ITEM ---
def cadastrar_item(request, subconjunto_id):
    sub = get_object_or_404(Subconjunto, id=subconjunto_id)
    
    # Passa o subconjunto_pai para o formulário filtrar as opções
    if request.method == 'POST':
        form = ItemForm(request.POST, subconjunto_pai=sub)
        if form.is_valid():
            item = form.save(commit=False)
            item.subconjunto = sub
            item.save()
            return redirect('detalhe_os', os_id=sub.conjunto.os.id)
    else:
        form = ItemForm(subconjunto_pai=sub)
        
    return render(request, 'main/form_generico.html', {'form': form, 'titulo': f'Novo Item (Subconjunto: {sub.acronimo_uu})'})

def editar_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    form = ItemForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        return redirect('detalhe_os', os_id=item.subconjunto.conjunto.os.id)
    return render(request, 'main/form_generico.html', {'form': form, 'titulo': f'Editar Item: {item.acronimo_tt}'})

def excluir_item(request, pk):
    item = get_object_or_404(Item, pk=pk)
    os_id = item.subconjunto.conjunto.os.id
    if request.method == 'POST':
        item.delete()
        return redirect('detalhe_os', os_id=os_id)
    return render(request, 'main/confirmar_exclusao.html', {'objeto': item.titulo_3 or item.acronimo_tt, 'tipo': 'Item'})

# --- DOCUMENTO (Informações) ---
def cadastrar_documento(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    form = DocumentoItemForm(request.POST or None, initial={'item': item})
    form.fields['item'].queryset = Item.objects.filter(id=item.id)
    
    if form.is_valid():
        doc = form.save(commit=False)
        doc.item = item
        doc.save()
        return redirect('detalhe_os', os_id=item.subconjunto.conjunto.os.id)
    return render(request, 'main/form_generico.html', {'form': form, 'titulo': f'Novo Documento para o Item {item.acronimo_tt}'})

def editar_documento(request, pk):
    doc = get_object_or_404(DocumentoItem, pk=pk)
    form = DocumentoItemForm(request.POST or None, instance=doc)
    form.fields['item'].queryset = Item.objects.filter(id=doc.item.id)
    
    if form.is_valid():
        form.save()
        return redirect('detalhe_os', os_id=doc.item.subconjunto.conjunto.os.id)
    return render(request, 'main/form_generico.html', {'form': form, 'titulo': f'Editar Informações do Documento: {doc.codigo_completo}'})

def excluir_documento(request, pk):
    doc = get_object_or_404(DocumentoItem, pk=pk)
    os_id = doc.item.subconjunto.conjunto.os.id
    if request.method == 'POST':
        doc.delete()
        
        return redirect('detalhe_os', os_id=os_id)
    return render(request, 'main/confirmar_exclusao.html', {'objeto': doc.codigo_completo, 'tipo': 'Documento'})

# --- GERENCIAR ARQUIVOS, STATUS E REVISÃO (Janela Separada) ---
def gerenciar_documento_arquivos(request, pk):
    doc = get_object_or_404(DocumentoItem, pk=pk)
    erro_validacao = None
    
    # Captura os valores originais do banco antes da submissão
    status_antigo = doc.status
    revisao_antiga = doc.revisao
    responsavel_antigo = doc.responsavel
    
    # === VALIDAÇÃO PREVENTIVA (AO ABRIR A TELA - GET) ===
    # Verifica se os arquivos apontados no banco realmente existem na pasta física. Se não existirem, limpa o campo!
    houve_correcao_banco = False

    if doc.caminho_editavel and not os.path.exists(doc.caminho_editavel):
        doc.caminho_editavel = None
        houve_correcao_banco = True

    if doc.caminho_pdf and not os.path.exists(doc.caminho_pdf):
        doc.caminho_pdf = None
        houve_correcao_banco = True

    if doc.caminho_adicional and not os.path.exists(doc.caminho_adicional):
        doc.caminho_adicional = None
        houve_correcao_banco = True

    # Varredura para encontrar caso exista fisicamente na pasta mas não estivesse mapeado
    pasta_alvo = doc.caminho_pasta
    codigo_base = doc.codigo_completo.upper()
    padrao_pdf = doc.nome_arquivo_padrao.upper()

    if os.path.exists(pasta_alvo):
        for arq in os.listdir(pasta_alvo):
            nome_base, ext = os.path.splitext(arq)
            caminho_completo_arq = os.path.join(pasta_alvo, arq)
            nome_up = nome_base.upper()
            ext_lower = ext.lower()

            # Se o editável não está preenchido, mas o arquivo existe na pasta
            if not doc.caminho_editavel and nome_up == codigo_base:
                permissoes_validas = [e.lower() for lista in EXTENSOES_EDITAVEIS_PERMITIDAS.values() for e in lista]
                if ext_lower in permissoes_validas:
                    doc.caminho_editavel = caminho_completo_arq
                    houve_correcao_banco = True

            # Se o PDF não está preenchido, mas o arquivo existe na pasta
            if not doc.caminho_pdf and nome_up == padrao_pdf:
                if ext_lower == '.pdf':
                    doc.caminho_pdf = caminho_completo_arq
                    houve_correcao_banco = True

    if houve_correcao_banco:
        doc.save()

    # Guarda os caminhos já corrigidos para o fluxo de POST
    caminho_editavel_antigo = doc.caminho_editavel
    caminho_pdf_antigo = doc.caminho_pdf
    caminho_adicional_antigo = doc.caminho_adicional
    
    if request.method == 'POST':
        form = DocumentoArquivosForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            documento = form.save(commit=False)
            
            # Preserva os caminhos antigos se nenhum arquivo novo foi enviado para aquele campo específico
            if not request.FILES.get('upload_editavel'):
                documento.caminho_editavel = caminho_editavel_antigo
            if not request.FILES.get('upload_pdf'):
                documento.caminho_pdf = caminho_pdf_antigo
            if not request.FILES.get('upload_adicional'):
                documento.caminho_adicional = caminho_adicional_antigo

            status_alterado = (documento.status != status_antigo)
            revisao_alterada = (documento.revisao != revisao_antiga)
            
            tem_upload_novo = bool(
                request.FILES.get('upload_editavel') or 
                request.FILES.get('upload_pdf') or 
                request.FILES.get('upload_adicional')
            )
            try:
                if status_alterado:
                    novo_responsavel = request.POST.get('responsavel')
                    if not novo_responsavel or novo_responsavel.strip() == "":
                        raise ValidationError(
                            "O status do documento foi alterado. É obrigatório selecionar um novo responsável."
                        )
                        
                if (status_alterado or revisao_alterada) and not tem_upload_novo:
                    arquivo_fisico_encontrado = False
                    if os.path.exists(pasta_alvo):
                        for arq in os.listdir(pasta_alvo):
                            nome_base, _ = os.path.splitext(arq)
                            if nome_base.upper() == padrao_pdf:
                                arquivo_fisico_encontrado = True
                                break
                    
                    if not arquivo_fisico_encontrado:
                        raise ValidationError(
                            f"Você alterou o Status ou a Revisão ('{documento.revisao}'). "
                            f"Não é permitido prosseguir sem anexar o arquivo correspondente ao padrão '{documento.nome_arquivo_padrao}.ext' "
                            f"ou sem garantir que ele já esteja na pasta física."
                        )

                # Processa novos uploads caso tenham sido enviados
                if request.FILES.get('upload_editavel'):
                    caminho = documento.tratar_upload_arquivo(request.FILES['upload_editavel'], tipo_campo='editavel')
                    if caminho: documento.caminho_editavel = caminho

                if request.FILES.get('upload_pdf'):
                    caminho = documento.tratar_upload_arquivo(request.FILES['upload_pdf'], tipo_campo='pdf')
                    if caminho: documento.caminho_pdf = caminho

                if request.FILES.get('upload_adicional'):
                    caminho = documento.tratar_upload_arquivo(request.FILES['upload_adicional'], tipo_campo='adicional')
                    if caminho: documento.caminho_adicional = caminho

                # Validação final de existência física pós-processamento
                if documento.caminho_editavel and not os.path.exists(documento.caminho_editavel):
                    documento.caminho_editavel = None
                if documento.caminho_pdf and not os.path.exists(documento.caminho_pdf):
                    documento.caminho_pdf = None

                documento.save()
                return redirect('detalhe_os', os_id=doc.item.subconjunto.conjunto.os.id)
            
            except ValidationError as e:
                erro_validacao = e.message if hasattr(e, 'message') else (e.messages[0] if hasattr(e, 'messages') else str(e))
    else:
        form = DocumentoArquivosForm(instance=doc)

    return render(request, 'main/form_gerenciar_arquivos.html', {
        'form': form, 
        'doc': doc,
        'erro_validacao': erro_validacao,
        'titulo': f'Gerenciar Arquivos e Status - {doc.codigo_completo}'
    })

def visualizar_pdf(request, pk):
    doc = get_object_or_404(DocumentoItem, pk=pk)
    if doc.caminho_pdf and os.path.exists(doc.caminho_pdf):
        return FileResponse(open(doc.caminho_pdf, 'rb'), content_type='application/pdf')
    raise Http404("Arquivo PDF não encontrado.")

def baixar_arquivo(request, pk, tipo):
    doc = get_object_or_404(DocumentoItem, pk=pk)
    caminho = doc.caminho_editavel if tipo == 'editavel' else doc.caminho_pdf
    
    if caminho and os.path.exists(caminho):
        return FileResponse(open(caminho, 'rb'), as_attachment=True)
    raise Http404("Arquivo não encontrado.")