# Melhorias na formatação de Excel no arquivo exportador.py

```python
import logging
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side, NamedStyle
from pathlib import Path
from datetime import datetime

def exportar_resultados(resultados, data_inicial, data_final):
    """
    Exporta os resultados extraídos para uma planilha .xlsx com formatação elegante.
    """
    if not resultados:
        logging.warning("⚠️ Nenhum dado a exportar. Nenhum arquivo será gerado.")
        return None

    wb = Workbook()
    ws = wb.active
    ws.title = "HC TJGO"

    # Estilos
    # Estilo para cabeçalho
    header_style = NamedStyle(name='header_style')
    header_style.font = Font(name="Arial", color="FFFFFF", bold=True, size=11)
    header_style.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_style.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    header_style.border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    wb.add_named_style(header_style)
    
    # Estilo para linhas pares
    even_row_style = NamedStyle(name='even_row_style')
    even_row_style.font = Font(name="Arial", size=10)
    even_row_style.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    even_row_style.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    even_row_style.border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    wb.add_named_style(even_row_style)
    
    # Estilo para linhas ímpares
    odd_row_style = NamedStyle(name='odd_row_style')
    odd_row_style.font = Font(name="Arial", size=10)
    odd_row_style.fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    odd_row_style.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
    odd_row_style.border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    wb.add_named_style(odd_row_style)

    # Cabeçalhos da planilha
    headers = ["Número CNJ", "Número do Processo", "Relator(a)", "Situação", "Data de Autuação"]
    ws.append(headers)

    # Aplicar estilos aos cabeçalhos
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.style = 'header_style'

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
            row_num = registros_validos + 2  # +2 porque a linha 1 é o cabeçalho
            
            # Adicionar dados
            ws.cell(row=row_num, column=1, value=item.get("numero_cnj", ""))
            ws.cell(row=row_num, column=2, value=item.get("numero_processo", ""))
            ws.cell(row=row_num, column=3, value=item.get("relator", ""))
            ws.cell(row=row_num, column=4, value=item.get("situacao", ""))
            ws.cell(row=row_num, column=5, value=item.get("data_autuacao", ""))
            
            # Aplicar estilos às células
            row_style = 'even_row_style' if registros_validos % 2 == 0 else 'odd_row_style'
            
            for col_num in range(1, 6):
                cell = ws.cell(row=row_num, column=col_num)
                cell.style = row_style
                
            registros_validos += 1
        except Exception as e:
            logging.error(f"❌ Erro ao processar item na posição {i}: {e}")

    if registros_validos == 0:
        logging.warning("⚠️ Nenhum registro válido foi exportado. Arquivo não será gerado.")
        return None

    # Ajuste da largura das colunas
    for i, coluna in enumerate(ws.columns, 1):
        max_length = max(len(str(cell.value)) if cell.value else 0 for cell in coluna)
        ws.column_dimensions[get_column_letter(i)].width = max(15, min(max_length + 2, 50))

    # Congelar linha do cabeçalho
    ws.freeze_panes = "A2"

    # Adicionar rodapé com informações
    row_rodape = registros_validos + 3
    
    # Estilo para rodapé - título
    footer_title_style = NamedStyle(name='footer_title_style')
    footer_title_style.font = Font(name="Arial", bold=True, size=10)
    footer_title_style.alignment = Alignment(horizontal="left", vertical="center")
    wb.add_named_style(footer_title_style)
    
    # Estilo para rodapé - valor
    footer_value_style = NamedStyle(name='footer_value_style')
    footer_value_style.font = Font(name="Arial", size=10)
    footer_value_style.alignment = Alignment(horizontal="left", vertical="center")
    wb.add_named_style(footer_value_style)
    
    # Adicionar linha de título do rodapé com formatação
    cell_title = ws.cell(row=row_rodape, column=1, value="Informações da Exportação:")
    cell_title.style = 'footer_title_style'
    
    # Adicionar linhas de dados do rodapé com formatação
    ws.cell(row=row_rodape + 1, column=1, value="Data da Busca:").style = 'footer_title_style'
    if data_inicial == data_final:
        ws.cell(row=row_rodape + 1, column=2, value=data_inicial).style = 'footer_value_style'
    else:
        ws.cell(row=row_rodape + 1, column=2, value=f"{data_inicial} a {data_final}").style = 'footer_value_style'
    
    ws.cell(row=row_rodape + 2, column=1, value="Total de Registros:").style = 'footer_title_style'
    ws.cell(row=row_rodape + 2, column=2, value=registros_validos).style = 'footer_value_style'
    
    ws.cell(row=row_rodape + 3, column=1, value="Data da Exportação:").style = 'footer_title_style'
    ws.cell(row=row_rodape + 3, column=2, value=datetime.now().strftime("%d/%m/%Y %H:%M:%S")).style = 'footer_value_style'

    # Define nome do arquivo
    def formatar(data):
        return data.replace("/", "-")

    if data_inicial == data_final:
        nome_arquivo = f"hc_tjgo_{formatar(data_inicial)}.xlsx"
    else:
        nome_arquivo = f"hc_tjgo_{formatar(data_inicial)}_a_{formatar(data_final)}.xlsx"

    # Salva arquivo na pasta dados_diarios
    caminho = Path("dados_diarios") / nome_arquivo
    Path("dados_diarios").mkdir(exist_ok=True)
    
    try:
        wb.save(caminho)
        logging.info(f"📁 Resultado salvo em: {caminho.resolve()}")
        return str(caminho)
    except Exception as e:
        logging.error(f"❌ Falha ao salvar arquivo {nome_arquivo}: {e}")
        return None
```

# Também é necessário melhorar o arquivo de planilha vazia em supabase/criar_xlsx_vazio.py

```python
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side, NamedStyle
from pathlib import Path
import sys
from datetime import datetime

def criar_xlsx_vazio(nome_arquivo):
    """
    Cria um arquivo Excel vazio com uma mensagem padrão e formatação melhorada
    """
    pasta = Path("dados_diarios")
    pasta.mkdir(parents=True, exist_ok=True)
    
    caminho_arquivo = pasta / nome_arquivo
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Rechecagem"
    
    # Criar estilos
    header_style = NamedStyle(name='header_style')
    header_style.font = Font(name="Arial", color="FFFFFF", bold=True, size=11)
    header_style.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_style.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    header_style.border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    wb.add_named_style(header_style)
    
    title_style = NamedStyle(name='title_style')
    title_style.font = Font(name="Arial", bold=True, size=10)
    title_style.alignment = Alignment(horizontal="left", vertical="center")
    title_style.border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    wb.add_named_style(title_style)
    
    value_style = NamedStyle(name='value_style')
    value_style.font = Font(name="Arial", size=10)
    value_style.alignment = Alignment(horizontal="left", vertical="center")
    value_style.border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    wb.add_named_style(value_style)
    
    # Adicionar cabeçalho
    ws.merge_cells('A1:B1')
    cell = ws.cell(row=1, column=1, value="RELATÓRIO DE RECHECAGEM - SEM DIVERGÊNCIAS")
    cell.style = 'header_style'
    
    # Adicionar informações sobre o arquivo
    ws.cell(row=2, column=1, value="Status da Rechecagem").style = 'title_style'
    ws.cell(row=2, column=2, value="Sem divergências detectadas").style = 'value_style'
    
    ws.cell(row=3, column=1, value="Data de Geração").style = 'title_style'
    ws.cell(row=3, column=2, value=datetime.now().strftime("%d/%m/%Y %H:%M:%S")).style = 'value_style'
    
    ws.cell(row=4, column=1, value="Informações").style = 'title_style'
    ws.cell(row=4, column=2, value="Este arquivo foi gerado automaticamente pelo processo de rechecagem").style = 'value_style'
    
    ws.cell(row=5, column=1, value="Observação").style = 'title_style'
    ws.cell(row=5, column=2, value="Nenhuma divergência foi encontrada entre os arquivos comparados").style = 'value_style'
    
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
```
