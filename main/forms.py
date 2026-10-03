from django import forms
from .models import OrdemServico, Conjunto, Subconjunto, Item, DocumentoItem, TIPO_DOCUMENTO_CHOICES, EXTENSOES_EDITAVEIS_PERMITIDAS

class OrdemServicoForm(forms.ModelForm):
    documentos_iniciais = forms.MultipleChoiceField(
        choices=TIPO_DOCUMENTO_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Selecionar Documentos Iniciais para a OS"
    )

    class Meta:
        model = OrdemServico
        fields = ['numero_os', 'descricao', 'criado_por', 'documentos_iniciais']

class ConjuntoForm(forms.ModelForm):
    class Meta:
        model = Conjunto
        fields = ['os', 'acronimo_vv', 'titulo_1', 'disciplina', 'criado_por']

class SubconjuntoForm(forms.ModelForm):
    class Meta:
        model = Subconjunto
        fields = ['conjunto', 'acronimo_uu', 'titulo_2', 'criado_por']

    def __init__(self, *args, **kwargs):
        conjunto_pai = kwargs.pop('conjunto_pai', None)
        super().__init__(*args, **kwargs)
        if conjunto_pai:
            # Restringe o campo apenas ao conjunto atual e o deixa pré-selecionado/oculto ou travado
            self.fields['conjunto'].queryset = Conjunto.objects.filter(pk=conjunto_pai.pk)
            self.fields['conjunto'].initial = conjunto_pai

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['subconjunto', 'acronimo_tt', 'titulo_3', 'criado_por']

    def __init__(self, *args, **kwargs):
        subconjunto_pai = kwargs.pop('subconjunto_pai', None)
        super().__init__(*args, **kwargs)
        if subconjunto_pai:
            # Restringe o campo apenas ao subconjunto atual
            self.fields['subconjunto'].queryset = Subconjunto.objects.filter(pk=subconjunto_pai.pk)
            self.fields['subconjunto'].initial = subconjunto_pai
            
class DocumentoItemForm(forms.ModelForm):
    class Meta:
        model = DocumentoItem
        fields = [
            'item', 
            'tipo_documento', 
            'responsavel', 
            'data_emissao_inicial', 
            'data_emissao_final', 
            'esconder_titulo_2', 
            'esconder_titulo_3', 
            'criado_por'
        ]
        widgets = {
            'data_emissao_inicial': forms.DateInput(attrs={'type': 'date'}),
            'data_emissao_final': forms.DateInput(attrs={'type': 'date'}),
        }

class DocumentoArquivosForm(forms.ModelForm):
    upload_editavel = forms.FileField(required=False, label="Enviar arquivo editável")
    upload_pdf = forms.FileField(required=False, label="Enviar arquivo PDF")
    upload_adicional = forms.FileField(required=False, label="Enviar arquivo adicional")

    class Meta:
        model = DocumentoItem
        fields = [
            'status', 
            'revisao', 
            'caminho_editavel', 
            'caminho_pdf', 
            'caminho_adicional'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            permitidas = EXTENSOES_EDITAVEIS_PERMITIDAS.get(self.instance.tipo_documento, [])
            if permitidas:
                self.fields['upload_editavel'].widget.attrs.update({
                    'accept': ','.join(permitidas)
                })
        
        self.fields['upload_pdf'].widget.attrs.update({'accept': '.pdf'})