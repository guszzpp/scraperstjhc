# exportador.py
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

def exportar_resultados(resultados, data_inicial, data_final):
    wb = Workbook()
    ws = wb.active
    ws.title = "HC TJGO"

    # Cabeçalhos
    headers = ["Número CNJ", "Número do Processo", "Relator(a)", "Situação", "Data de Autuação"]
    ws.append(headers)

    for item in resultados:
        ws.append([
            item.get("numero_cnj", ""),
            item.get("numero_processo", ""),
            item.get("relator", ""),
            item.get("situacao", ""),
            item.get("data_autuacao", "")
        ])

    # Ajustar largura das colunas
    for i, coluna in enumerate(ws.columns, 1):
        max_length = max(len(str(c.value)) if c.value else 0 for c in coluna)
        ws.column_dimensions[get_column_letter(i)].width = max(20, max_length + 2)

    def formatar(data): return data.replace("/", "-")

    if data_inicial == data_final:
        nome_arquivo = f"hc_tjgo_{formatar(data_inicial)}.xlsx"
    else:
        nome_arquivo = f"hc_tjgo_{formatar(data_inicial)}_a_{formatar(data_final)}.xlsx"

    wb.save(nome_arquivo)
    print(f"\n📁 Resultado salvo em '{nome_arquivo}' com {len(resultados)} registros.")
    return nome_arquivo
