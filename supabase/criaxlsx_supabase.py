from openpyxl import Workbook
from pathlib import Path
from datetime import datetime, timedelta

# Calcula a data de ontem
data_ontem = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")

# Define a pasta onde salvar
pasta = Path("dados_diarios")
pasta.mkdir(parents=True, exist_ok=True)

# Define o caminho completo do arquivo
caminho_arquivo = pasta / f"hc_tjgo_{data_ontem}.xlsx"

# Cria um novo arquivo XLSX
wb = Workbook()
ws = wb.active
ws.title = "Sheet1"
ws['A1'] = "Arquivo gerado automaticamente para upload"

# Salva o arquivo
wb.save(caminho_arquivo)

print(f"Arquivo {caminho_arquivo} criado com sucesso.")