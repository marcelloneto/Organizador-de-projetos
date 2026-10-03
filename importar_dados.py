import os
import json
from datetime import datetime
import django

# Configura o ambiente do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'organizador.settings')  # Substitua pelo nome do seu projeto se necessário
django.setup()

from main.models import OrdemServico, Conjunto, Subconjunto, Item, DocumentoItem

def importar_json_para_django(caminho_json="dados_migracao.json"):
    if not os.path.exists(caminho_json):
        print(f"Arquivo JSON não encontrado: {caminho_json}")
        return

    with open(caminho_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    contador = 0
    for linha in dados:
        os_num = linha.get("os_numero")
        descricao_os = linha.get("descricao_os")
        
        if not os_num:
            continue

        # 1. Garante que a Ordem de Serviço existe
        os_obj, _ = OrdemServico.objects.get_or_create(
            numero_os=os_num,
            defaults={
                "descricao": descricao_os or f"OS {os_num}",
                "criado_por": "Marcello Neto"
            }
        )

        # 2. Garante que o Conjunto existe (Chave correta no JSON é 'titulo_1')[cite: 13]
        conj_vv = linha.get("conjunto_vv") or "01"
        titulo_1 = linha.get("titulo_1")  # Corrigido de 'conjunto_titulo_1'[cite: 12, 13]
        disciplina = linha.get("disciplina") or "MEC"

        conjunto_obj, _ = Conjunto.objects.get_or_create(
            os=os_obj,
            acronimo_vv=conj_vv,
            defaults={
                "titulo_1": titulo_1,
                "disciplina": 'GER' if disciplina == 'GERAL' else 'MEC',
                "criado_por": "Marcello Neto"
            }
        )
        # Atualiza o título caso já exista incorreto no banco
        if conjunto_obj.titulo_1 != titulo_1 and titulo_1 is not None:
            conjunto_obj.titulo_1 = titulo_1
            conjunto_obj.save()

        # 3. Garante que o Subconjunto existe (Chave correta no JSON é 'titulo_2')[cite: 13]
        sub_uu = linha.get("subconjunto_uu") or "01"
        titulo_2 = linha.get("titulo_2")  # Corrigido de 'subconjunto_titulo_2'[cite: 12, 13]

        subconjunto_obj, _ = Subconjunto.objects.get_or_create(
            conjunto=conjunto_obj,
            acronimo_uu=sub_uu,
            defaults={
                "titulo_2": titulo_2,
                "criado_por": "Marcello Neto"
            }
        )
        if subconjunto_obj.titulo_2 != titulo_2 and titulo_2 is not None:
            subconjunto_obj.titulo_2 = titulo_2
            subconjunto_obj.save()

        # 4. Garante que o Item existe (Chave correta no JSON é 'titulo_3')[cite: 13]
        item_tt = linha.get("item_tt") or "01"
        titulo_3 = linha.get("titulo_3")  # Corrigido de 'item_titulo_3'[cite: 12, 13]

        item_obj, _ = Item.objects.get_or_create(
            subconjunto=subconjunto_obj,
            acronimo_tt=item_tt,
            defaults={
                "titulo_3": titulo_3,
                "criado_por": "Marcello Neto"
            }
        )
        if item_obj.titulo_3 != titulo_3 and titulo_3 is not None:
            item_obj.titulo_3 = titulo_3
            item_obj.save()

        # 5. Cria ou Atualiza o DocumentoItem
        acronimo_tipo = linha.get("acronimo_tipo")
        revisao = linha.get("revisao") or "R00"
        responsavel = linha.get("responsavel")
        
        data_cronograma = linha.get("data_cronograma")
        data_emissao = linha.get("data_emissao_inicial")

        def parse_data(data_str):
            if data_str and isinstance(data_str, str) and len(data_str) == 10:  # Formato YYYY-MM-DD
                try:
                    return datetime.strptime(data_str, "%Y-%m-%d").date()
                except ValueError:
                    pass
            return None

        DocumentoItem.objects.update_or_create(
            item=item_obj,
            tipo_documento=acronimo_tipo,
            revisao=revisao,
            defaults={
                "responsavel": responsavel if responsavel in ['Rebeca Palma', 'Marcello Neto', 'Bruno Romano', 'Fábio Watanabe'] else 'Marcello Neto',
                "data_emissao_final": parse_data(data_cronograma),
                "data_emissao_inicial": parse_data(data_emissao),
                "criado_por": "Marcello Neto"
            }
        )
        contador += 1

    print(f"Importação concluída! {contador} registros processados e salvos no banco de dados com sucesso.")

if __name__ == '__main__':
    importar_json_para_django()