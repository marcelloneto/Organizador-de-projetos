from django.shortcuts import render, redirect, get_object_or_404
from .models import OrdemServico, Conjunto, Subconjunto, Item, DocumentoItem, EXTENSOES_EDITAVEIS_PERMITIDAS
from .forms import OrdemServicoForm, ConjuntoForm, SubconjuntoForm, ItemForm, DocumentoItemForm, DocumentoArquivosForm
import os
from django.http import Http404, FileResponse
from django.core.exceptions import ValidationError
from django.db.models import Q


def lista_os_view(request):
    ordens_servico = OrdemServico.objects.all().order_by('-id')
    return render(request, 'main/lista_os.html', {'ordens_servico': ordens_servico})

def detalhe_os_view(request, os_id):
    os_obj = get_object_or_404(OrdemServico, id=os_id)
    
    # 1. Captura múltiplos valores dos filtros da barra lateral
    conjuntos_selecionados_list = request.GET.getlist('conjunto')
    tipos_selecionados_list = request.GET.getlist('tipo_doc')
    responsaveis_selecionados_list = request.GET.getlist('responsavel')
    etapas_selecionadas_list = request.GET.getlist('etapa') # Novo filtro de etapa
    
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
        print(f"conjunto: {conjunto}")
        subconjuntos_lista = []
        for sub in subconjuntos:
            itens = sub.itens.all().order_by('acronimo_tt')
            print(f"subconjunto: {sub}")
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
                
                documentos = documentos.order_by('tipo_documento')
                
                if not (termo_busca or tipos_selecionados_list or responsaveis_selecionados_list or etapas_selecionadas_list) or documentos.exists():
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
        print(sub)
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
        print(doc)
        return redirect('detalhe_os', os_id=os_id)
    return render(request, 'main/confirmar_exclusao.html', {'objeto': doc.codigo_completo, 'tipo': 'Documento'})

# --- GERENCIAR ARQUIVOS, STATUS E REVISÃO (Janela Separada) ---
def gerenciar_documento_arquivos(request, pk):
    doc = get_object_or_404(DocumentoItem, pk=pk)
    erro_validacao = None
    
    # Captura os valores originais do banco antes da submissão
    status_antigo = doc.status
    revisao_antiga = doc.revisao
    
    if request.method == 'POST':
        form = DocumentoArquivosForm(request.POST, request.FILES, instance=doc)
        if form.is_valid():
            documento = form.save(commit=False)
            
            # Detecta alterações em Status ou Revisão
            status_alterado = (documento.status != status_antigo)
            revisao_alterada = (documento.revisao != revisao_antiga)
            
            # Verifica se algum arquivo novo foi enviado no formulário
            tem_upload_novo = bool(
                request.FILES.get('upload_editavel') or 
                request.FILES.get('upload_pdf') or 
                request.FILES.get('upload_adicional')
            )
            
            try:
                # REGRA RÍGIDA: Se houve alteração de Status OU de Revisão, 
                # é obrigatório o upload novo OU o arquivo físico da nova revisão já existir na pasta.
                if (status_alterado or revisao_alterada) and not tem_upload_novo:
                    pasta_alvo = documento.caminho_pasta
                    padrao_novo = documento.nome_arquivo_padrao.upper()
                    arquivo_fisico_encontrado = False
                    
                    if os.path.exists(pasta_alvo):
                        for arq in os.listdir(pasta_alvo):
                            nome_base, _ = os.path.splitext(arq)
                            if nome_base.upper() == padrao_novo:
                                arquivo_fisico_encontrado = True
                                break
                    
                    if not arquivo_fisico_encontrado:
                        raise ValidationError(
                            f"Você alterou o Status ou a Revisão ('{documento.revisao}'). "
                            f"Não é permitido prosseguir sem anexar o arquivo correspondente ao padrão '{documento.nome_arquivo_padrao}.ext' "
                            f"ou sem garantir que ele já esteja na pasta física."
                        )

                # Processa os uploads caso tenham sido enviados
                if request.FILES.get('upload_editavel'):
                    caminho = documento.tratar_upload_arquivo(request.FILES['upload_editavel'], tipo_campo='editavel')
                    if caminho: documento.caminho_editavel = caminho

                if request.FILES.get('upload_pdf'):
                    caminho = documento.tratar_upload_arquivo(request.FILES['upload_pdf'], tipo_campo='pdf')
                    if caminho: documento.caminho_pdf = caminho

                if request.FILES.get('upload_adicional'):
                    caminho = documento.tratar_upload_arquivo(request.FILES['upload_adicional'], tipo_campo='adicional')
                    if caminho: documento.caminho_adicional = caminho

                # Varredura automática caso nenhum arquivo novo tenha sido enviado, mas os dados mudaram de forma válida
                pasta_alvo = documento.caminho_pasta
                padrao_busca = documento.nome_arquivo_padrao.upper()

                if os.path.exists(pasta_alvo) and not tem_upload_novo:
                    arquivos_na_pasta = os.listdir(pasta_alvo)
                    
                    for arq in arquivos_na_pasta:
                        nome_base, ext = os.path.splitext(arq)
                        if nome_base.upper() == padrao_busca:
                            if ext.lower() in [e.lower() for lista in EXTENSOES_EDITAVEIS_PERMITIDAS.values() for e in lista]:
                                documento.caminho_editavel = os.path.join(pasta_alvo, arq)
                            elif ext.lower() == '.pdf':
                                documento.caminho_pdf = os.path.join(pasta_alvo, arq)

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