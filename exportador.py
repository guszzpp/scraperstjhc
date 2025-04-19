# exportador.py

import logging
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from pathlib import Path

def exportar_resultados(resultados, data_inicial, data_final):
    """
    Exporta os resultados extraídos para uma planilha .xlsx com formatação adequada.
    """

    if not resultados:
        logging.warning("⚠️ Nenhum dado a exportar. Nenhum arquivo será gerado.")
        return None

    wb = Workbook()
    ws = wb.active
    ws.title = "HC TJGO"

    # Cabeçalhos da planilha
    headers = ["Número CNJ", "Número do Processo", "Relator(a)", "Situação", "Data de Autuação"]
    ws.append(headers)

    # Preenchimento das linhas
    registros_validos = 0
    for i, item in enumerate(resultados):
        if item is None:
            logging.warning(f"❗ Registro nulo na posição {i}. Ignorado.")
            continue

        if not isinstance(item, dict):
            logging.warning(f"❗ Registro inválido na posição {i} (tipo {type(item)}). Ignorado.")
            continue

        try:
            ws.append([
                item.get("numero_cnj", ""),
                item.get("numero_processo", ""),
                item.get("relator", ""),
                item.get("situacao", ""),
                item.get("data_autuacao", "")
            ])
            registros_validos += 1
        except Exception as e:
            logging.error(f"❌ Erro ao processar item na posição {i}: {e}")

    if registros_validos == 0:
        logging.warning("⚠️ Nenhum registro válido foi exportado. Arquivo não será gerado.")
        return None

    # Ajuste da largura das colunas
    for i, coluna in enumerate(ws.columns, 1):
        max_length = max(len(str(cell.value)) if cell.value else 0 for cell in coluna)
        ws.column_dimensions[get_column_letter(i)].width = max(20, max_length + 2)

    # Define nome do arquivo
    def formatar(data):
        return data.replace("/", "-")

    if data_inicial == data_final:
        nome_arquivo = f"hc_tjgo_{formatar(data_inicial)}.xlsx"
    else:
        nome_arquivo = f"hc_tjgo_{formatar(data_inicial)}_a_{formatar(data_final)}.xlsx"

    # Salva arquivo na pasta atual
    caminho = Path(nome_arquivo)
    try:
        wb.save(caminho)
        logging.info(f"📁 Resultado salvo em: {caminho.resolve()}")
        return str(caminho)
    except Exception as e:
        logging.error(f"❌ Falha ao salvar arquivo {nome_arquivo}: {e}")
        return None
