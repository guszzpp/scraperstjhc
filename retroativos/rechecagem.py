import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pandas as pd
from datetime import datetime
from pathlib import Path

from email_detalhado import preparar_email_alerta_retroativos

def comparar_arquivos(arquivo_anteontem, arquivo_ontem):
    """
    Compara dois arquivos Excel de HCs e identifica divergências.
    Retorna:
    - True se houver divergência
    - False se não houver divergência
    - Salva detalhes das divergências em um arquivo Excel separado
    """
    try:
        # Carregar os arquivos Excel
        df_anteontem = pd.read_excel(arquivo_anteontem)
        df_ontem = pd.read_excel(arquivo_ontem)
        
        print(f"Arquivo de anteontem: {arquivo_anteontem} - {len(df_anteontem)} registros")
        print(f"Arquivo de ontem: {arquivo_ontem} - {len(df_ontem)} registros")
        
        # Verificar se os dataframes estão vazios
        if df_anteontem.empty and df_ontem.empty:
            print("Ambos os arquivos estão vazios. Não há divergência.")
            return False
            
        # Se um estiver vazio e o outro não, há divergência
        if df_anteontem.empty and not df_ontem.empty:
            print("Arquivo de anteontem está vazio, mas arquivo de ontem contém dados. Há divergência.")
            with open("divergencias.txt", "w") as f:
                f.write("Arquivo de anteontem está vazio, mas arquivo de ontem contém dados.")
            df_ontem.to_excel("dados_diarios/divergencias.xlsx", index=False)
            return True
            
        if not df_anteontem.empty and df_ontem.empty:
            print("Arquivo de ontem está vazio, mas arquivo de anteontem contém dados. Há divergência.")
            with open("divergencias.txt", "w") as f:
                f.write("Arquivo de ontem está vazio, mas arquivo de anteontem contém dados.")
            df_anteontem.to_excel("dados_diarios/divergencias.xlsx", index=False)
            return True
        
        # Verificar se as colunas são as mesmas
        if set(df_anteontem.columns) != set(df_ontem.columns):
            print("As colunas dos arquivos são diferentes. Há divergência.")
            with open("divergencias.txt", "w") as f:
                f.write("As colunas dos arquivos são diferentes.\n")
                f.write(f"Colunas de anteontem: {list(df_anteontem.columns)}\n")
                f.write(f"Colunas de ontem: {list(df_ontem.columns)}\n")
            return True
        
        # Verificar o número de processos
        if len(df_anteontem) != len(df_ontem):
            print(f"Número de processos diferente: Anteontem ({len(df_anteontem)}) vs Ontem ({len(df_ontem)})")
            
        # Usar a coluna "Número do Processo" como chave para identificar os mesmos processos
        chave = "Número do Processo"
        if chave not in df_anteontem.columns or chave not in df_ontem.columns:
            print(f"Coluna '{chave}' não encontrada em um dos arquivos")
            with open("divergencias.txt", "w") as f:
                f.write(f"Coluna '{chave}' não encontrada em um dos arquivos.\n")
            return True
            
        # Verificar processos que estão em ontem mas não em anteontem (novos)
        processos_anteontem = set(df_anteontem[chave])
        processos_ontem = set(df_ontem[chave])
        
        novos_processos = processos_ontem - processos_anteontem
        removidos_processos = processos_anteontem - processos_ontem
        
        if novos_processos:
            print(f"Há {len(novos_processos)} novos processos em ontem que não estavam em anteontem")
            df_novos = df_ontem[df_ontem[chave].isin(novos_processos)]
            df_novos.to_excel("dados_diarios/novos_processos.xlsx", index=False)
            with open("divergencias.txt", "w") as f:
                f.write(f"Há {len(novos_processos)} novos processos em ontem que não estavam em anteontem.\n")
                for processo in novos_processos:
                    f.write(f"- {processo}\n")
            
        if removidos_processos:
            print(f"Há {len(removidos_processos)} processos em anteontem que não estão mais em ontem")
            df_removidos = df_anteontem[df_anteontem[chave].isin(removidos_processos)]
            df_removidos.to_excel("dados_diarios/processos_removidos.xlsx", index=False)
            
            # Adicionar informações ao arquivo de divergências
            with open("divergencias.txt", "a" if novos_processos else "w") as f:
                f.write(f"Há {len(removidos_processos)} processos em anteontem que não estão mais em ontem.\n")
                for processo in removidos_processos:
                    f.write(f"- {processo}\n")
        
        # Verificar se há alterações em processos que estão em ambos os arquivos
        processos_comuns = processos_anteontem.intersection(processos_ontem)
        
        alteracoes = []
        for processo in processos_comuns:
            row_anteontem = df_anteontem[df_anteontem[chave] == processo].iloc[0]
            row_ontem = df_ontem[df_ontem[chave] == processo].iloc[0]
            
            for coluna in df_anteontem.columns:
                if row_anteontem[coluna] != row_ontem[coluna]:
                    alteracoes.append({
                        "Processo": processo,
                        "Coluna": coluna,
                        "Valor Anteontem": row_anteontem[coluna],
                        "Valor Ontem": row_ontem[coluna]
                    })
        
        if alteracoes:
            print(f"Há {len(alteracoes)} alterações em processos que estão em ambos os arquivos")
            df_alteracoes = pd.DataFrame(alteracoes)
            df_alteracoes.to_excel("dados_diarios/alteracoes.xlsx", index=False)
            
            # Adicionar informações ao arquivo de divergências
            modo = "a" if novos_processos or removidos_processos else "w"
            with open("divergencias.txt", modo) as f:
                f.write(f"Há {len(alteracoes)} alterações em processos que estão em ambos os arquivos.\n")
                for alteracao in alteracoes:
                    f.write(f"- {alteracao['Processo']} ({alteracao['Coluna']}): {alteracao['Valor Anteontem']} -> {alteracao['Valor Ontem']}\n")
        
        # Determinar se há divergência
        tem_divergencia = bool(novos_processos or removidos_processos or alteracoes)
        
        # Salvar resultado
        with open("tem_divergencia.txt", "w") as f:
            f.write("true" if tem_divergencia else "false")
            
        # Preparar relatório de divergências se houver alguma
        if tem_divergencia:
            gerar_relatorio_divergencias(
                novos_processos=novos_processos, 
                removidos_processos=removidos_processos, 
                alteracoes=alteracoes,
                df_ontem=df_ontem,
                df_anteontem=df_anteontem,
                chave=chave
            )
            
        # Preparar e-mail
        if tem_divergencia:
            df_divergentes = pd.read_excel("dados_diarios/novos_processos.xlsx") if Path("dados_diarios/novos_processos.xlsx").exists() else pd.DataFrame()
            preparar_email_alerta_retroativos(df_divergentes)
        else:
            preparar_email_alerta_retroativos(None)

        return tem_divergencia
        
    except Exception as e:
        print(f"Erro ao comparar arquivos: {e}")
        with open("erro_rechecagem.txt", "w") as f:
            f.write(f"Erro ao comparar arquivos: {e}")
        with open("tem_divergencia.txt", "w") as f:
            f.write("error")
        return True  # Retorna True para garantir que um e-mail seja enviado em caso de erro

def gerar_relatorio_divergencias(novos_processos, removidos_processos, alteracoes, df_ontem, df_anteontem, chave):
    """
    Gera um relatório detalhado das divergências encontradas
    """
    try:
        # Criar um DataFrame com todas as divergências
        divergencias = []
        
        # Adicionar novos processos
        for processo in novos_processos:
            dados = df_ontem[df_ontem[chave] == processo].iloc[0].to_dict()
            dados["Tipo_Divergencia"] = "Novo processo"
            dados["Descrição"] = "Processo encontrado em ontem, mas não em anteontem"
            divergencias.append(dados)
            
        # Adicionar processos removidos
        for processo in removidos_processos:
            dados = df_anteontem[df_anteontem[chave] == processo].iloc[0].to_dict()
            dados["Tipo_Divergencia"] = "Processo removido"
            dados["Descrição"] = "Processo encontrado em anteontem, mas não em ontem"
            divergencias.append(dados)
            
        # Adicionar alterações
        processos_alterados = set(item["Processo"] for item in alteracoes)
        for processo in processos_alterados:
            alteracoes_processo = [item for item in alteracoes if item["Processo"] == processo]
            descricao = ", ".join([f"{item['Coluna']}: {item['Valor Anteontem']} -> {item['Valor Ontem']}" for item in alteracoes_processo])
            
            dados = df_ontem[df_ontem[chave] == processo].iloc[0].to_dict()
            dados["Tipo_Divergencia"] = "Alteração"
            dados["Descrição"] = descricao
            divergencias.append(dados)
            
        # Criar DataFrame de divergências e salvar
        if divergencias:
            df_divergencias = pd.DataFrame(divergencias)
            
            # Reordenar colunas para colocar Tipo_Divergencia e Descrição no início
            colunas = ["Tipo_Divergencia", "Descrição"] + [col for col in df_divergencias.columns if col not in ["Tipo_Divergencia", "Descrição"]]
            df_divergencias = df_divergencias[colunas]
            
            # Salvar relatório detalhado
            df_divergencias.to_excel("dados_diarios/relatorio_divergencias.xlsx", index=False)
            print(f"Relatório de divergências gerado com {len(divergencias)} registros")
            return True
    except Exception as e:
        print(f"Erro ao gerar relatório de divergências: {e}")
    return False

def main():
    if len(sys.argv) < 3:
        print("Uso: python rechecagem_melhorada.py <data_anteontem> <data_ontem>")
        print("Exemplo: python rechecagem_melhorada.py 01/04/2025 02/04/2025")
        sys.exit(1)
        
    data_anteontem = sys.argv[1]
    data_ontem = sys.argv[2]
    
    # Converter datas para formato DD-MM-YYYY para nomes dos arquivos
    try:
        data_anteontem_obj = datetime.strptime(data_anteontem, "%d/%m/%Y")
        data_ontem_obj = datetime.strptime(data_ontem, "%d/%m/%Y")
        
        data_anteontem_fmt = data_anteontem_obj.strftime("%d-%m-%Y")
        data_ontem_fmt = data_ontem_obj.strftime("%d-%m-%Y")
    except ValueError:
        print("Erro: Formato de data inválido. Use DD/MM/YYYY")
        sys.exit(1)
    
    # Verificar se os arquivos existem
    path_anteontem = Path(f"dados_diarios/hc_tjgo_{data_anteontem_fmt}.xlsx")
    path_ontem = Path(f"dados_diarios/hc_tjgo_{data_ontem_fmt}.xlsx")
    
    if not path_anteontem.exists():
        print(f"Erro: Arquivo {path_anteontem} não encontrado")
        with open("erro_rechecagem.txt", "w") as f:
            f.write(f"Arquivo {path_anteontem} não encontrado")
        with open("tem_divergencia.txt", "w") as f:
            f.write("error")
        sys.exit(1)
        
    if not path_ontem.exists():
        print(f"Erro: Arquivo {path_ontem} não encontrado")
        with open("erro_rechecagem.txt", "w") as f:
            f.write(f"Arquivo {path_ontem} não encontrado")
        with open("tem_divergencia.txt", "w") as f:
            f.write("error")
        sys.exit(1)
    
    # Comparar os arquivos
    tem_divergencia = comparar_arquivos(path_anteontem, path_ontem)
    
    print(f"Resultado da rechecagem: {'Divergência encontrada' if tem_divergencia else 'Sem divergências'}")
    return 0

if __name__ == "__main__":
    main()