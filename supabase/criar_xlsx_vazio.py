from openpyxl import Workbook
from pathlib import Path
import sys

def criar_xlsx_vazio(nome_arquivo):
    """
    Cria um arquivo Excel vazio com uma mensagem padrão
    """
    pasta = Path("dados_diarios")
    pasta.mkdir(parents=True, exist_ok=True)
    
    caminho_arquivo = pasta / nome_arquivo
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Rechecagem"
    
    # Adicionar informações sobre o arquivo
    ws['A1'] = "Status da Rechecagem"
    ws['B1'] = "Sem divergências detectadas"
    
    ws['A2'] = "Data de Geração"
    ws['B2'] = "=TODAY()"
    
    ws['A3'] = "Informações"
    ws['B3'] = "Este arquivo foi gerado automaticamente pelo processo de rechecagem"
    
    ws['A4'] = "Observação"
    ws['B4'] = "Nenhuma divergência foi encontrada entre os arquivos comparados"
    
    # Ajustar largura das colunas
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 60
    
    # Salvar o arquivo
    wb.save(caminho_arquivo)
    print(f"Arquivo {caminho_arquivo} criado com sucesso.")
    return str(caminho_arquivo)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python criar_xlsx_vazio.py <nome_arquivo>")
        sys.exit(1)
        
    nome_arquivo = sys.argv[1]
    criar_xlsx_vazio(nome_arquivo)