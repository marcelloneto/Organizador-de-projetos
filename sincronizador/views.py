import os
import json
import datetime
import tempfile
from django.shortcuts import render
from django.http import JsonResponse

def index(request):
    return render(request, 'sincronizador/index.html')

def read_properties(request):
    if request.method == 'POST':
        try:
            # Se recebermos o caminho diretamente (ou via form)
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            file_path = data.get('filepath')
            
            # Se vier via FormData com ficheiro, lê do diretório de rede configurado
            if not file_path and 'file' in request.FILES:
                file = request.FILES['file']
                filename = file.name
                
                # Lê o caminho da pasta de rede a partir do .txt
                target_dir = r"K:\Engenharia\CLIENTES\INSIGHT ENERGY - INTERNOS\INSIGHT MÁQUINA DE CORTAR CONDUTOR\03-Desenvolvimento\01-Modelo 3D"
                txt_path = os.path.abspath('caminho_pasta.txt')
                if os.path.exists(txt_path):
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        linha = f.read().strip()
                        if linha:
                            target_dir = linha
                            
                file_path = os.path.normpath(os.path.join(target_dir, filename))

            if not file_path or not os.path.exists(file_path):
                return JsonResponse({'error': f'O ficheiro não foi encontrado no caminho: {file_path}'}, status=400)

            filename = os.path.basename(file_path)
            ext = filename.split('.')[-1].lower()
            doc_type = 2 if ext == 'sldasm' else 1

            properties = {}
            json_matched_data = {}
            
            try:
                if os.path.exists('dados.json'):
                    with open('dados.json', 'r', encoding='utf-8') as f:
                        dados_banco = json.load(f)
                        for item in dados_banco:
                            codigo = item.get("codigo", "")
                            if codigo and codigo.upper() in filename.upper():
                                json_matched_data = item.copy()
                                break
                    
                    if json_matched_data.get("Revisão Atual") == "00":
                        data_hoje = datetime.date.today().strftime("%d/%m/%Y")
                        for chave in json_matched_data.keys():
                            if "DATA" in chave.upper():
                                json_matched_data[chave] = data_hoje
            except Exception as json_err:
                print(f"Aviso JSON: {json_err}")

            swApp = None
            model_title = None

            try:
                import win32com.client
                import pythoncom
                pythoncom.CoInitialize()
                
                swApp = win32com.client.Dispatch("SldWorks.Application")
                swApp.Visible = False 
                
                err = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                warn = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                
                # Abre diretamente da rede com modo 3 (leitura restrita)
                swModel = swApp.OpenDoc6(file_path, doc_type, 3, "", err, warn)
                if isinstance(swModel, tuple):
                    swModel = swModel[0]
                
                if swModel:
                    title_attr = swModel.GetTitle
                    model_title = title_attr() if callable(title_attr) else title_attr
                    
                    configs_attr = swModel.GetConfigurationNames
                    configurations = configs_attr() if callable(configs_attr) else configs_attr
                    configs_to_check = [""]
                    if configurations:
                        configs_to_check.extend(list(configurations))
                    
                    for config in configs_to_check:
                        swCustPropMgr = swModel.Extension.CustomPropertyManager(config)
                        if swCustPropMgr.Count > 0:
                            names_attr = swCustPropMgr.GetNames
                            names = names_attr() if callable(names_attr) else names_attr
                            
                            if names:
                                for name in names:
                                    try:
                                        prop_value = swModel.GetCustomInfoValue(config, name)
                                        if not prop_value or prop_value.strip() == "":
                                            prop_value = swModel.CustomInfo2(config, name)
                                        properties[name] = str(prop_value) if prop_value else ""
                                    except:
                                        properties[name] = ""
                    
                    try:
                        swMassProp = swModel.Extension.CreateMassProperty()
                        if swMassProp:
                            properties["--- DADOS FÍSICOS ---"] = "-----------------------------------"
                            properties["Massa (kg)"] = str(round(swMassProp.Mass, 4))
                            properties["Volume (m³)"] = str(round(swMassProp.Volume, 6))
                            properties["Área de Superfície (m²)"] = str(round(swMassProp.SurfaceArea, 4))
                    except:
                        pass
                else:
                    return JsonResponse({'error': f'O modelo não abriu. Caminho: {file_path} | Erro SW: {err.value}'}, status=500)
                    
            except Exception as e:
                properties['Erro de Sistema'] = str(e)
                
            finally:
                try:
                    if swApp and model_title:
                        swApp.CloseDoc(model_title)
                    elif swApp:
                        swApp.CloseDoc(filename)
                except:
                    pass

            return JsonResponse({
                'filename': filename, 
                'filepath': file_path,
                'properties': properties,
                'json_data': json_matched_data
            })
            
        except Exception as main_e:
            return JsonResponse({'error': str(main_e)}, status=500)
            
    return JsonResponse({'error': 'Método inválido.'}, status=405)

def write_properties(request):
    if request.method == 'POST':
        try:
            # Recebe o nome do ficheiro ou os dados enviados
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            filename = data.get('filename')
            updates = data.get('updates')
            
            if not filename:
                # Caso venha via FormData com ficheiro
                if 'file' in request.FILES:
                    file = request.FILES['file']
                    filename = file.name
                    updates = json.loads(request.POST.get('updates', '{}'))
                else:
                    return JsonResponse({'error': 'Nome do ficheiro em falta.'}, status=400)

            # Lê o diretório de destino a partir do ficheiro .txt
            target_dir = r"K:\Engenharia\CLIENTES\INSIGHT ENERGY - INTERNOS\INSIGHT MÁQUINA DE CORTAR CONDUTOR\03-Desenvolvimento\01-Modelo 3D"
            txt_path = os.path.abspath('caminho_pasta.txt')
            if os.path.exists(txt_path):
                try:
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        linha = f.read().strip()
                        if linha:
                            target_dir = linha
                except Exception as e_txt:
                    print(f"Aviso ao ler caminho_pasta.txt: {e_txt}")

            file_path = os.path.normpath(os.path.join(target_dir, filename))

            if not os.path.exists(file_path):
                return JsonResponse({'error': f'Ficheiro não encontrado na rede: {file_path}'}, status=400)

            ext = filename.split('.')[-1].lower()
            doc_type = 2 if ext == 'sldasm' else 1
            
            swApp = None

            try:
                import win32com.client
                import pythoncom
                pythoncom.CoInitialize()
                
                swApp = win32com.client.Dispatch("SldWorks.Application")
                swApp.Visible = True  
                
                err = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                warn = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                
                # Abre diretamente o ficheiro existente na rede em modo de escrita (1)
                swModel = swApp.OpenDoc6(file_path, doc_type, 1, "", err, warn)
                if isinstance(swModel, tuple):
                    swModel = swModel[0]
                    
                if swModel:
                    configs_attr = swModel.GetConfigurationNames
                    configurations = configs_attr() if callable(configs_attr) else configs_attr
                    configs_to_write = [""] 
                    if configurations:
                        configs_to_write.extend(list(configurations))
                    
                    for prop_name, new_val in updates.items():
                        for cfg in configs_to_write:
                            swCustPropMgr = swModel.Extension.CustomPropertyManager(cfg)
                            
                            if prop_name.strip().upper() == "MATERIAL" and str(new_val).strip() != "":
                                try:
                                    swModel.SetMaterialPropertyName2(cfg, "", str(new_val))
                                    formula_material = f'"SW-Material@{filename}"'
                                    swCustPropMgr.Add3(prop_name, 30, formula_material, 2)
                                    swCustPropMgr.Set(prop_name, formula_material)
                                except Exception as e_mat:
                                    print(f"Erro material: {e_mat}")
                            else:
                                val_str = "" if new_val is None else str(new_val)
                                swCustPropMgr.Add3(prop_name, 30, val_str, 2)
                                swCustPropMgr.Set(prop_name, val_str)
                    
                    swModel.ForceRebuild3(False) 
                    
                    err_save = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                    warn_save = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
                    
                    # Salva diretamente no caminho original da rede
                    swModel.Save3(1, err_save, warn_save)
                    swApp.CloseDoc(filename)
                    
                    return JsonResponse({'success': True, 'message': 'Ficheiro atualizado e guardado na rede com sucesso.'})
                else:
                    return JsonResponse({'error': f'Não foi possível abrir o modelo para gravação. Erro SW: {err.value}'}, status=500)

            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
                
        except Exception as main_e:
            return JsonResponse({'error': str(main_e)}, status=500)
            
    return JsonResponse({'error': 'Método inválido.'}, status=405)