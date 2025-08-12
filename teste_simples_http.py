#!/usr/bin/env python3
"""
Teste simples para verificar se a página do STJ está acessível
Usa apenas requisições HTTP, sem necessidade de navegador
"""

import requests
import time
import logging
from urllib.parse import urlparse
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('teste_http.log', encoding='utf-8')
    ]
)

def test_stj_page_http():
    """
    Testa se a página do STJ está acessível via HTTP
    """
    logging.info("🚀 Iniciando teste HTTP da página do STJ")
    
    url = "https://processo.stj.jus.br/processo/pesquisa/?aplicacao=processos.ea"
    
    # Headers para simular um navegador real
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        logging.info(f"🌐 Testando acesso à URL: {url}")
        
        # Fazer a requisição
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=30)
        end_time = time.time()
        
        # Verificar status da resposta
        logging.info(f"📊 Status da resposta: {response.status_code}")
        logging.info(f"⏱️ Tempo de resposta: {end_time - start_time:.2f} segundos")
        
        if response.status_code == 200:
            logging.info("✅ Página acessível (status 200)")
        else:
            logging.error(f"❌ Página retornou status {response.status_code}")
            return False
        
        # Verificar headers da resposta
        logging.info("📋 Headers da resposta:")
        for key, value in response.headers.items():
            logging.info(f"   {key}: {value}")
        
        # Verificar conteúdo da página
        content = response.text
        content_length = len(content)
        logging.info(f"📄 Tamanho do conteúdo: {content_length} caracteres")
        
        # Verificar se a página contém elementos importantes
        logging.info("🔍 Verificando elementos na página:")
        
        # Verificar título
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
            logging.info(f"✅ Título encontrado: {title}")
        else:
            logging.warning("⚠️ Título não encontrado")
        
        # Verificar se contém elementos do formulário
        elementos_procurados = [
            'idDataAutuacaoInicial',
            'idDataAutuacaoFinal',
            'dataAutuacaoInicial',
            'dataAutuacaoFinal',
            'idBotaoPesquisarFormularioExtendido',
            'idOrgaosOrigemCampoParaPesquisar'
        ]
        
        elementos_encontrados = 0
        for elemento in elementos_procurados:
            if elemento in content:
                logging.info(f"✅ Elemento '{elemento}' encontrado no HTML")
                elementos_encontrados += 1
            else:
                logging.warning(f"⚠️ Elemento '{elemento}' não encontrado")
        
        # Verificar se contém palavras-chave do STJ
        palavras_chave = ['STJ', 'Superior Tribunal de Justiça', 'processo', 'pesquisa']
        for palavra in palavras_chave:
            if palavra.lower() in content.lower():
                logging.info(f"✅ Palavra-chave '{palavra}' encontrada")
            else:
                logging.warning(f"⚠️ Palavra-chave '{palavra}' não encontrada")
        
        # Verificar se é uma página de formulário
        if '<form' in content.lower():
            logging.info("✅ Página contém formulário")
        else:
            logging.warning("⚠️ Página não contém formulário")
        
        # Verificar se há inputs
        inputs_count = len(re.findall(r'<input[^>]*>', content, re.IGNORECASE))
        logging.info(f"✅ Encontrados {inputs_count} elementos input")
        
        # Verificar se há JavaScript
        if '<script' in content.lower():
            logging.info("✅ Página contém JavaScript")
        else:
            logging.warning("⚠️ Página não contém JavaScript")
        
        # Salvar conteúdo para análise
        with open('pagina_stj.html', 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info("💾 Conteúdo da página salvo em 'pagina_stj.html'")
        
        # Resumo do teste
        logging.info("📋 RESUMO DO TESTE HTTP:")
        logging.info(f"   - Status: {response.status_code}")
        logging.info(f"   - Tempo de resposta: {end_time - start_time:.2f}s")
        logging.info(f"   - Tamanho do conteúdo: {content_length} chars")
        logging.info(f"   - Elementos específicos encontrados: {elementos_encontrados}/{len(elementos_procurados)}")
        logging.info(f"   - Inputs encontrados: {inputs_count}")
        
        # Critérios de sucesso
        sucesso = (
            response.status_code == 200 and
            elementos_encontrados >= 2 and  # Pelo menos 2 elementos específicos
            inputs_count > 0 and
            content_length > 1000  # Página tem conteúdo significativo
        )
        
        if sucesso:
            logging.info("✅ TESTE HTTP PASSOU - Página está acessível e contém elementos esperados")
            return True
        else:
            logging.error("❌ TESTE HTTP FALHOU - Página não atende aos critérios mínimos")
            return False
            
    except requests.exceptions.Timeout:
        logging.error("❌ Timeout na requisição - página demorou muito para responder")
        return False
    except requests.exceptions.ConnectionError:
        logging.error("❌ Erro de conexão - não foi possível conectar ao servidor")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erro na requisição: {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Erro inesperado: {e}")
        return False

def test_url_redirects():
    """
    Testa se há redirecionamentos na URL
    """
    logging.info("🔄 Testando redirecionamentos...")
    
    url = "https://processo.stj.jus.br/processo/pesquisa/?aplicacao=processos.ea"
    
    try:
        # Fazer requisição sem seguir redirecionamentos
        response = requests.get(url, allow_redirects=False, timeout=10)
        
        if response.status_code in [301, 302, 303, 307, 308]:
            logging.warning(f"⚠️ URL redireciona para: {response.headers.get('Location', 'N/A')}")
            return False
        else:
            logging.info("✅ URL não redireciona")
            return True
            
    except Exception as e:
        logging.error(f"❌ Erro ao testar redirecionamentos: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Teste HTTP da página do STJ")
    print("=" * 50)
    
    # Testar redirecionamentos
    redirect_ok = test_url_redirects()
    
    # Testar acesso à página
    sucesso = test_stj_page_http()
    
    print("\n" + "=" * 50)
    if sucesso and redirect_ok:
        print("🎉 Teste HTTP concluído com SUCESSO!")
        print("✅ A página do STJ está acessível e contém os elementos esperados")
    else:
        print("💥 Teste HTTP concluído com FALHA!")
        print("❌ Há problemas com o acesso à página do STJ")
    
    print("\n📄 Log detalhado salvo em: teste_http.log")
    print("💾 Conteúdo da página salvo em: pagina_stj.html")
