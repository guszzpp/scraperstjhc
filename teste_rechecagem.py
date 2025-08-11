# teste_rechecagem.py
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta
import os

def criar_arquivos_teste():
    """
    Cria arquivos de teste para simular D+1 e D+2
    """
    hoje = datetime.now()
    data_d1 = hoje - timedelta(days=1)
    data_d2 = hoje
    
    nome_data_d1 = data_d1.strftime("%d-%m-%Y")
    nome_data_d2 = data_d2.strftime("%d-%m-%Y")
    
    # Dados de teste para D+1 (primeira raspagem)
    dados_d1 = [
        {
            "Número do Processo": "1234567-89.2024.8.09.0000",
            "Classe": "HC",
            "Data Autuação": "01/01/2024",
            "Origem": "TJGO",
            "Relator": "Ministro Teste 1",
            "Órgão Julgador": "Primeira Turma",
            "Data Julgamento": "15/01/2024",
            "Data Publicação": "20/01/2024"
        },
        {
            "Número do Processo": "2345678-90.2024.8.09.0000",
            "Classe": "HC",
            "Data Autuação": "02/01/2024",
            "Origem": "TJGO",
            "Relator": "Ministro Teste 2",
            "Órgão Julgador": "Segunda Turma",
            "Data Julgamento": "16/01/2024",
            "Data Publicação": "21/01/2024"
        }
    ]
    
    # Dados de teste para D+2 (segunda raspagem) - inclui um novo HC
    dados_d2 = [
        {
            "Número do Processo": "1234567-89.2024.8.09.0000",
            "Classe": "HC",
            "Data Autuação": "01/01/2024",
            "Origem": "TJGO",
            "Relator": "Ministro Teste 1",
            "Órgão Julgador": "Primeira Turma",
            "Data Julgamento": "15/01/2024",
            "Data Publicação": "20/01/2024"
        },
        {
            "Número do Processo": "2345678-90.2024.8.09.0000",
            "Classe": "HC",
            "Data Autuação": "02/01/2024",
            "Origem": "TJGO",
            "Relator": "Ministro Teste 2",
            "Órgão Julgador": "Segunda Turma",
            "Data Julgamento": "16/01/2024",
            "Data Publicação": "21/01/2024"
        },
        {
            "Número do Processo": "3456789-91.2024.8.09.0000",  # NOVO HC
            "Classe": "HC",
            "Data Autuação": "03/01/2024",
            "Origem": "TJGO",
            "Relator": "Ministro Teste 3",
            "Órgão Julgador": "Terceira Turma",
            "Data Julgamento": "17/01/2024",
            "Data Publicação": "22/01/2024"
        }
    ]
    
    # Criar diretório se não existir
    os.makedirs("dados_diarios", exist_ok=True)
    
    # Salvar arquivo D+1
    df_d1 = pd.DataFrame(dados_d1)
    arquivo_d1 = f"dados_diarios/hc_tjgo_{nome_data_d1}.xlsx"
    df_d1.to_excel(arquivo_d1, index=False)
    print(f"✅ Arquivo D+1 criado: {arquivo_d1}")
    
    # Salvar arquivo D+2
    df_d2 = pd.DataFrame(dados_d2)
    arquivo_d2 = f"dados_diarios/hc_tjgo_{nome_data_d2}.xlsx"
    df_d2.to_excel(arquivo_d2, index=False)
    print(f"✅ Arquivo D+2 criado: {arquivo_d2}")
    
    return data_d2.strftime("%d/%m/%Y")

def testar_rechecagem():
    """
    Testa a rechecagem com dados simulados
    """
    print("🧪 Iniciando teste de rechecagem...")
    
    # Criar arquivos de teste
    data_teste = criar_arquivos_teste()
    
    # Executar rechecagem
    print(f"🚀 Executando rechecagem para {data_teste}...")
    
    try:
        from retroativos.rechecagem import rechecagem_retroativa
        rechecagem_retroativa(data_teste)
        
        # Verificar se os arquivos de saída foram criados
        if os.path.exists("novos_retroativos.xlsx"):
            print("✅ Arquivo 'novos_retroativos.xlsx' criado com sucesso!")
            df_novos = pd.read_excel("novos_retroativos.xlsx")
            print(f"   📊 {len(df_novos)} novos HCs detectados")
        else:
            print("❌ Arquivo 'novos_retroativos.xlsx' não foi criado")
        
        if os.path.exists("email_subject.txt"):
            with open("email_subject.txt", "r", encoding="utf-8") as f:
                subject = f.read().strip()
            print(f"📧 Assunto do e-mail: {subject}")
        
        if os.path.exists("email_body.txt"):
            with open("email_body.txt", "r", encoding="utf-8") as f:
                body = f.read().strip()
            print(f"📧 Corpo do e-mail: {body[:100]}...")
        
        print("✅ Teste de rechecagem concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_rechecagem()

