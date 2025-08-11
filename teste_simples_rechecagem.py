# teste_simples_rechecagem.py
import os
import sys
from datetime import datetime, timedelta

def verificar_arquivos_rechecagem():
    """
    Verifica se os arquivos necessários para rechecagem existem
    """
    hoje = datetime.now()
    data_d1 = hoje - timedelta(days=1)
    data_d2 = hoje
    
    nome_data_d1 = data_d1.strftime("%d-%m-%Y")
    nome_data_d2 = data_d2.strftime("%d-%m-%Y")
    
    arquivo_d1_xlsx = f"dados_diarios/hc_tjgo_{nome_data_d1}.xlsx"
    arquivo_d1_csv = f"dados_diarios/resultados_{nome_data_d1}.csv"
    arquivo_d2_xlsx = f"dados_diarios/hc_tjgo_{nome_data_d2}.xlsx"
    arquivo_d2_csv = f"dados_diarios/resultados_{nome_data_d2}.csv"
    
    print("🔍 Verificando arquivos para rechecagem:")
    print(f"   📁 D+1 ({data_d1.strftime('%d/%m/%Y')}):")
    print(f"      - XLSX: {arquivo_d1_xlsx} {'✅' if os.path.exists(arquivo_d1_xlsx) else '❌'}")
    print(f"      - CSV:  {arquivo_d1_csv} {'✅' if os.path.exists(arquivo_d1_csv) else '❌'}")
    print(f"   📁 D+2 ({data_d2.strftime('%d/%m/%Y')}):")
    print(f"      - XLSX: {arquivo_d2_xlsx} {'✅' if os.path.exists(arquivo_d2_xlsx) else '❌'}")
    print(f"      - CSV:  {arquivo_d2_csv} {'✅' if os.path.exists(arquivo_d2_csv) else '❌'}")
    
    arquivo_d1_existe = os.path.exists(arquivo_d1_xlsx) or os.path.exists(arquivo_d1_csv)
    arquivo_d2_existe = os.path.exists(arquivo_d2_xlsx) or os.path.exists(arquivo_d2_csv)
    
    if arquivo_d1_existe and arquivo_d2_existe:
        print("\n✅ Ambos os arquivos existem! A rechecagem pode ser executada.")
        print(f"   Execute: python retroativos/executor_rechecagem.py")
        return True
    else:
        print("\n❌ Arquivos insuficientes para rechecagem.")
        if not arquivo_d1_existe:
            print(f"   Execute primeiro: python main.py {data_d1.strftime('%d/%m/%Y')}")
        if not arquivo_d2_existe:
            print(f"   Execute primeiro: python main.py {data_d2.strftime('%d/%m/%Y')}")
        return False

def listar_arquivos_dados_diarios():
    """
    Lista todos os arquivos na pasta dados_diarios
    """
    print("\n📁 Arquivos em dados_diarios:")
    if not os.path.exists("dados_diarios"):
        print("   ❌ Pasta dados_diarios não existe!")
        return
    
    arquivos = os.listdir("dados_diarios")
    if not arquivos:
        print("   📭 Pasta vazia")
        return
    
    for arquivo in sorted(arquivos):
        caminho = os.path.join("dados_diarios", arquivo)
        tamanho = os.path.getsize(caminho)
        modificado = datetime.fromtimestamp(os.path.getmtime(caminho))
        print(f"   📄 {arquivo} ({tamanho} bytes, {modificado.strftime('%d/%m/%Y %H:%M')})")

def main():
    print("🧪 Teste Simples de Rechecagem")
    print("=" * 50)
    
    # Verificar arquivos
    pode_executar = verificar_arquivos_rechecagem()
    
    # Listar arquivos existentes
    listar_arquivos_dados_diarios()
    
    # Instruções
    print("\n📋 Instruções:")
    print("1. Para executar rechecagem automática:")
    print("   python retroativos/executor_rechecagem.py")
    print("\n2. Para executar rechecagem manual:")
    print("   python retroativos/executor_rechecagem.py DD/MM/AAAA")
    print("\n3. Para executar raspagem:")
    print("   python main.py DD/MM/AAAA")
    
    if pode_executar:
        print("\n✅ Sistema pronto para rechecagem!")
    else:
        print("\n⚠️ Execute as raspagens primeiro!")

if __name__ == "__main__":
    main()
