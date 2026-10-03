import os
import django

# Configura o ambiente do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'organizador.settings')  # Substitua 'seu_projeto' pelo nome real do seu projeto
django.setup()

from main.models import OrdemServico, Conjunto, Subconjunto, Item

def inspecionar_banco():
    print("=" * 60)
    print("INSPEÇÃO DO BANCO DE DADOS - HIERARQUIA DE PROJETOS")
    print("=" * 60)

    ordens = OrdemServico.objects.all()
    if not ordens.exists():
        print("Nenhuma Ordem de Serviço encontrada no banco de dados.")
        return

    for os in ordens:
        print(f"\n[OS] Nº: {os.numero_os} | Descrição: {os.descricao}")
        
        conjuntos = os.conjuntos.all().order_by('acronimo_vv')
        if not conjuntos.exists():
            print("   └── (Sem conjuntos cadastrados)")
            continue

        for conj in conjuntos:
            print(f"   └── Conjunto [{conj.acronimo_vv}] - {conj.titulo_1} (Disciplina: {conj.disciplina})")
            
            subconjuntos = conj.subconjuntos.all().order_by('acronimo_uu')
            if not subconjuntos.exists():
                print(f"        └── (Sem subconjuntos)")
                continue

            for sub in subconjuntos:
                print(f"        └── Subconjunto [{sub.acronimo_uu}] - {sub.titulo_2}")
                
                itens = sub.itens.all().order_by('acronimo_tt')
                if not itens.exists():
                    print(f"             └── (Sem itens)")
                    continue

                for item in itens:
                    print(f"             └── Item [{item.acronimo_tt}] - {item.titulo_3}")
                    
                    # Opcional: listar documentos do item se quiser ver a ponta final
                    documentos = item.documentos.all()
                    for doc in documentos:
                        print(f"                  📄 Doc: {doc.codigo_completo} (Rev: {doc.revisao}) - Status: {doc.status}")

    print("\n" + "=" * 60)
    print("Fim da inspeção.")
    print("=" * 60)

if __name__ == '__main__':
    inspecionar_banco()