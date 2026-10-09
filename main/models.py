import os
import shutil
from datetime import datetime, date
from django.db import models
from django.core.exceptions import ValidationError

CAMINHO_BASE_PROJETOS = r"K:\Engenharia\CLIENTES\INSIGHT ENERGY - INTERNOS"

CRIADOR_CHOICES = [
    ('Rebeca Palma', 'Rebeca Palma'),
    ('Marcello Neto', 'Marcello Neto'),
    ('Bruno Romano', 'Bruno Romano'),
    ('Fábio Watanabe', 'Fábio Watanabe'),
    ('Ricardo Ferreira', 'Ricardo Ferreira'),
]

DISCIPLINA_CHOICES = [
    ('GER', 'Geral'),
    ('MEC', 'Mecânica'),
]

TIPO_DOCUMENTO_CHOICES = [
    ('RT', 'Relatório técnico'),
    ('DT', 'Desenho técnico'),
    ('CRO', 'Cronograma'),
    ('PRO', 'Procedimento'),
    ('PO.PRO', 'Procedimento da produção'),
    ('IT.PRO', 'Instrução de trabalho da produção'),
    ('LM', 'Lista de Materiais'),
    ('PIT', 'Plano de Inspeção e teste'),
    ('DB', 'DataBook'),
    ('MC', 'Memorial de cálculo'),
]

EXTENSOES_EDITAVEIS_PERMITIDAS = {
    'RT': ['.docx', '.doc'],
    'DT': ['.slddrw', '.idw'],
    'CRO': ['.xlsx', '.xls', '.docx', '.doc', '.pptx', '.ppt'],
    'PRO': ['.docx', '.doc'],
    'PO.PRO': ['.docx', '.doc'],
    'IT.PRO': ['.docx', '.doc'],
    'LM': ['.xlsx', '.xls', '.docx', '.doc'],
    'PIT': ['.xlsx', '.xls', '.docx', '.doc'],
    'DB': ['.xlsx', '.xls', '.docx', '.doc'],
    'MC': ['.docx', '.doc'],
}

STATUS_DOCUMENTO_CHOICES = [
    ('Não iniciado', 'Não iniciado'),
    ('Em elaboração', 'Em elaboração'),
    ('Em revisão', 'Em revisão'),
    ('Em análise', 'Em análise'),
    ('Para aprovação', 'Para aprovação'),
    ('Aprovado', 'Aprovado'),
    ('Em fabricação', 'Em fabricação'),
    ('Cancelado', 'Cancelado'),
]

REVISAO_CHOICES = [(f"R{i:02d}", f"R{i:02d}") for i in range(9)]

def executar_backup_e_exclusao_pasta(caminho_pasta_alvo):
    
    if caminho_pasta_alvo and os.path.exists(caminho_pasta_alvo):
        diretorio_pai = os.path.dirname(caminho_pasta_alvo)
        nome_pasta_original = os.path.basename(caminho_pasta_alvo)
        
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        nome_pasta_backup = f"{nome_pasta_original}_{timestamp}"
        caminho_backup = os.path.join(diretorio_pai, nome_pasta_backup)
        
        try:
            shutil.copytree(caminho_pasta_alvo, caminho_backup)
            shutil.rmtree(caminho_pasta_alvo)
            return caminho_backup
        except Exception as e:
            print(f"Erro ao realizar backup físico no Explorer: {e}")
    return None


class OrdemServico(models.Model):
    numero_os = models.CharField(max_length=50, unique=True, verbose_name="Ordem de Serviço (OS - YYYY)")
    descricao = models.CharField(max_length=200, verbose_name="Descrição da OS")
    criado_por = models.CharField(max_length=50, choices=CRIADOR_CHOICES, verbose_name="Criado por")
    criado_em = models.DateTimeField(auto_now_add=True)

    @property
    def caminho_pasta(self):
        nome_pasta = f"OS-{self.numero_os} - {self.descricao}".upper()
        return os.path.join(CAMINHO_BASE_PROJETOS, nome_pasta)

    def clean(self):
        super().clean()
        if self.numero_os:
            qs = OrdemServico.objects.filter(numero_os__iexact=self.numero_os.strip())
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({"numero_os": f"Já existe uma Ordem de Serviço cadastrada com o número '{self.numero_os}'."})
        
        if self.descricao:
            qs_desc = OrdemServico.objects.filter(descricao__iexact=self.descricao.strip())
            if self.pk:
                qs_desc = qs_desc.exclude(pk=self.pk)
            if qs_desc.exists():
                raise ValidationError({"descricao": f"Já existe uma Ordem de Serviço cadastrada com a descrição '{self.descricao}'."})

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            os.makedirs(self.caminho_pasta, exist_ok=True)

    def delete(self, *args, **kwargs):
        executar_backup_e_exclusao_pasta(self.caminho_pasta)
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.numero_os


class Conjunto(models.Model):
    os = models.ForeignKey(OrdemServico, on_delete=models.CASCADE, related_name='conjuntos', verbose_name="Ordem de Serviço")
    acronimo_vv = models.CharField(max_length=10, verbose_name="Nº do Conjunto (VV)")
    titulo_1 = models.CharField(max_length=150, verbose_name="Título 1 (Nome do Conjunto)", blank=True, null=True)
    disciplina = models.CharField(max_length=10, choices=DISCIPLINA_CHOICES, default='MEC', verbose_name="Disciplina")
    criado_por = models.CharField(max_length=50, choices=CRIADOR_CHOICES, verbose_name="Criado por")

    class Meta:
        unique_together = ('os', 'acronimo_vv')

    @property
    def caminho_pasta(self):
        nome_pasta = f"{self.acronimo_vv} - {self.titulo_1}".upper()
        return os.path.join(self.os.caminho_pasta, nome_pasta)

    def clean(self):
        super().clean()
        if self.os_id:
            qs = Conjunto.objects.filter(os=self.os)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            if qs.filter(acronimo_vv__iexact=self.acronimo_vv.strip()).exists():
                raise ValidationError({"acronimo_vv": f"Já existe um Conjunto com o acrônimo '{self.acronimo_vv}' nesta OS."})
            
            if self.titulo_1 and qs.filter(titulo_1__iexact=self.titulo_1.strip()).exists():
                raise ValidationError({"titulo_1": f"Já existe um Conjunto com o título '{self.titulo_1}' nesta OS."})

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            os.makedirs(self.caminho_pasta, exist_ok=True)

    def delete(self, *args, **kwargs):
        executar_backup_e_exclusao_pasta(self.caminho_pasta)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Conjunto {self.acronimo_vv} - {self.titulo_1}"


class Subconjunto(models.Model):
    conjunto = models.ForeignKey(Conjunto, on_delete=models.CASCADE, related_name='subconjuntos', verbose_name="Conjunto")
    acronimo_uu = models.CharField(max_length=10, verbose_name="Nº do Subconjunto (UU)")
    titulo_2 = models.CharField(max_length=150, blank=True, null=True, verbose_name="Título 2 (Opcional)")
    criado_por = models.CharField(max_length=50, choices=CRIADOR_CHOICES, verbose_name="Criado por")

    def clean(self):
        super().clean()
        if self.conjunto_id:
            qs = Subconjunto.objects.filter(conjunto=self.conjunto)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            if qs.filter(acronimo_uu__iexact=self.acronimo_uu.strip()).exists():
                raise ValidationError({"acronimo_uu": f"Já existe um Subconjunto com o acrônimo '{self.acronimo_uu}' neste Conjunto."})
            
            if self.titulo_2 and qs.filter(titulo_2__iexact=self.titulo_2.strip()).exists():
                raise ValidationError({"titulo_2": f"Já existe um Subconjunto com o título '{self.titulo_2}' neste Conjunto."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        for item in self.itens.all():
            for doc in item.documentos.all():
                pasta = doc.caminho_pasta
                if pasta and os.path.exists(pasta):
                    executar_backup_e_exclusao_pasta(pasta)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"Subconjunto {self.acronimo_uu} {('- ' + self.titulo_2) if self.titulo_2 else ''}"


class Item(models.Model):
    subconjunto = models.ForeignKey(Subconjunto, on_delete=models.CASCADE, related_name='itens', verbose_name="Subconjunto")
    acronimo_tt = models.CharField(max_length=10, verbose_name="Nº do Item (TT)")
    titulo_3 = models.CharField(max_length=150, blank=True, null=True, verbose_name="Título 3 (Opcional)")
    criado_por = models.CharField(max_length=50, choices=CRIADOR_CHOICES, verbose_name="Criado por")

    def clean(self):
        super().clean()
        if self.subconjunto_id:
            qs = Item.objects.filter(subconjunto=self.subconjunto)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            if qs.filter(acronimo_tt__iexact=self.acronimo_tt.strip()).exists():
                raise ValidationError({"acronimo_tt": f"Já existe um Item com o acrônimo '{self.acronimo_tt}' neste Subconjunto."})
            
            if self.titulo_3 and qs.filter(titulo_3__iexact=self.titulo_3.strip()).exists():
                raise ValidationError({"titulo_3": f"Já existe um Item com o título '{self.titulo_3}' neste Subconjunto."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Item {self.acronimo_tt} {('- ' + self.titulo_3) if self.titulo_3 else ''}"


class DocumentoItem(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='documentos', verbose_name="Item")
    tipo_documento = models.CharField(max_length=20, choices=TIPO_DOCUMENTO_CHOICES, verbose_name="Tipo de Documento (XXX)")
    criado_por = models.CharField(max_length=50, choices=CRIADOR_CHOICES, verbose_name="Criado por")
    
    esconder_titulo_2 = models.BooleanField(default=False, verbose_name="Ocultar Título 2")
    esconder_titulo_3 = models.BooleanField(default=False, verbose_name="Ocultar Título 3")

    status = models.CharField(max_length=30, choices=STATUS_DOCUMENTO_CHOICES, default='Não iniciado', verbose_name="Status do Documento")
    revisao = models.CharField(max_length=5, choices=REVISAO_CHOICES, default='R00', verbose_name="Revisão Atual (XX)")
    
    responsavel = models.CharField(max_length=50, choices=CRIADOR_CHOICES, blank=True, null=True, verbose_name="Responsável")
    data_emissao_inicial = models.DateField(blank=True, null=True, verbose_name="Data de Emissão Inicial")
    data_emissao_final = models.DateField(blank=True, null=True, verbose_name="Data de Emissão Final")

    caminho_editavel = models.CharField(max_length=500, blank=True, null=True, verbose_name="Caminho do editável")
    caminho_pdf = models.CharField(max_length=500, blank=True, null=True, verbose_name="Caminho do PDF")
    caminho_adicional = models.CharField(max_length=500, blank=True, null=True, verbose_name="Caminho adicional")

    @property
    def codigo_completo(self):
        xxx = self.tipo_documento
        yyyy = self.item.subconjunto.conjunto.os.numero_os.split('.')[0] if self.item.subconjunto.conjunto.os.numero_os else ""
        vv = self.item.subconjunto.conjunto.acronimo_vv
        uu = self.item.subconjunto.acronimo_uu
        tt = self.item.acronimo_tt
        return f"{xxx}.{yyyy}.{vv}.{uu}.{tt}"

    @property
    def nome_arquivo_padrao(self):
        return f"{self.codigo_completo}-{self.revisao}"

    @property
    def caminho_pasta(self):
        conjunto = self.item.subconjunto.conjunto
        sub = self.item.subconjunto
        
        dict_docs = dict(TIPO_DOCUMENTO_CHOICES)
        nome_tipo = dict_docs.get(self.tipo_documento, self.tipo_documento)
        caminho_atual = os.path.join(conjunto.caminho_pasta, f"{self.tipo_documento} - {nome_tipo}".upper())
        
        if sub.titulo_2 and str(sub.titulo_2).strip():
            nome_sub = f"{sub.acronimo_uu} - {sub.titulo_2}".upper()
            caminho_atual = os.path.join(caminho_atual, nome_sub)
            
        return caminho_atual

    def clean(self):
        super().clean()
        if self.item_id and self.tipo_documento:
            qs = DocumentoItem.objects.filter(item=self.item, tipo_documento=self.tipo_documento)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError(f"Já existe um documento do tipo '{self.get_tipo_documento_display()}' cadastrado para este Item.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def tratar_upload_arquivo(self, arquivo_upload, tipo_campo='editavel'):
        if not arquivo_upload:
            return None

        nome_arquivo_enviado, ext = os.path.splitext(arquivo_upload.name)
        ext = ext.lower()

        if tipo_campo == 'editavel':
            permitidas = EXTENSOES_EDITAVEIS_PERMITIDAS.get(self.tipo_documento, [])
            if permitidas and ext not in permitidas:
                raise ValidationError(f"A extensão '{ext}' não é permitida para o tipo de documento. Permitidas: {', '.join(permitidas)}")
        elif tipo_campo == 'pdf':
            if ext != '.pdf':
                raise ValidationError("O arquivo enviado para o PDF precisa ser estritamente no formato .pdf")
        if tipo_campo != "editavel":
            if nome_arquivo_enviado.upper() != self.nome_arquivo_padrao.upper():
                raise ValidationError(f"O nome do arquivo enviado deve seguir rigorosamente o padrão: '{self.nome_arquivo_padrao}{ext}'")
        else:
            if nome_arquivo_enviado.upper() != self.codigo_completo.upper():
                raise ValidationError(f"O nome do arquivo enviado deve seguir rigorosamente o padrão: '{self.nome_arquivo_padrao}{ext}'")

        conjunto = self.item.subconjunto.conjunto
        sub = self.item.subconjunto
        
        os.makedirs(conjunto.os.caminho_pasta, exist_ok=True)
        os.makedirs(conjunto.caminho_pasta, exist_ok=True)
        
        dict_docs = dict(TIPO_DOCUMENTO_CHOICES)
        nome_tipo = dict_docs.get(self.tipo_documento, self.tipo_documento)
        pasta_tipo = os.path.join(conjunto.caminho_pasta, f"{self.tipo_documento} - {nome_tipo}".upper())
        os.makedirs(pasta_tipo, exist_ok=True)
        
        pasta_destino = pasta_tipo
        if sub.titulo_2 and str(sub.titulo_2).strip():
            nome_sub = f"{sub.acronimo_uu} - {sub.titulo_2}".upper()
            pasta_destino = os.path.join(pasta_tipo, nome_sub)
            
        os.makedirs(pasta_destino, exist_ok=True)
        
        # Se for um arquivo editável, o nome não leva a revisão. Se for PDF ou outro, mantém o padrão com revisão.
        if tipo_campo == 'editavel':
            nome_base_arquivo = f"{self.codigo_completo}{ext}"
        else:
            nome_base_arquivo = f"{self.nome_arquivo_padrao}{ext}"
            
        caminho_destino_final = os.path.join(pasta_destino, nome_base_arquivo)

        if os.path.exists(caminho_destino_final):
            self.mover_para_obsoleto(caminho_destino_final, pasta_destino)

        with open(caminho_destino_final, 'wb+') as destino:
            for chunk in arquivo_upload.chunks():
                destino.write(chunk)

        return caminho_destino_final

    def mover_para_obsoleto(self, caminho_arquivo_atual, pasta_destino):
        pasta_obsoleto = os.path.join(pasta_destino, "OBSOLETO")
        os.makedirs(pasta_obsoleto, exist_ok=True)

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        nome_arq, ext = os.path.splitext(os.path.basename(caminho_arquivo_atual))
        novo_nome = f"{nome_arq}_{timestamp}{ext}"
        caminho_obsoleto = os.path.join(pasta_obsoleto, novo_nome)

        shutil.move(caminho_arquivo_atual, caminho_obsoleto)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    @property
    def alerta_prazo(self):
        if not self.data_emissao_final:
            return None
        dias_restantes = (self.data_emissao_final - date.today()).days
        if dias_restantes > 3:
            return 'green'
        elif 2 <= dias_restantes <= 3:
            return 'yellow'
        else:
            return 'red'

    @property
    def nome_completo_formatado(self):
        t1 = self.item.subconjunto.conjunto.os.descricao
        if self.item.subconjunto.conjunto.titulo_1 is None:
            t2 = ""
        else:
            t2 = self.item.subconjunto.conjunto.titulo_1
        t3 = "" if self.esconder_titulo_3 else self.item.titulo_3
        dict_docs = dict(TIPO_DOCUMENTO_CHOICES)
        t4 = dict_docs.get(self.tipo_documento, self.tipo_documento)

        partes = [p.strip() for p in [t1, t2, t3, t4] if p and str(p).strip()]
        return " - ".join(partes).upper()

    @property
    def nome_arquivo_pdf_atual(self):
        if self.caminho_pdf:
            return os.path.basename(self.caminho_pdf)
        return ""

    @property
    def nome_arquivo_editavel_atual(self):
        if self.caminho_editavel:
            return os.path.basename(self.caminho_editavel)
        return ""
    
    @property
    def nome_arquivo_adicional_atual(self):
        if self.caminho_adicional:
            return os.path.basename(self.caminho_adicional)
        return ""

    def __str__(self):

        return f"{self.codigo_completo} ({self.revisao})"