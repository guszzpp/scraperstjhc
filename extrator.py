# extrator.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extrair_detalhes_processo(driver, wait, titulo="Processo"):
    try:
        # Classe e número do processo
        classe_span = wait.until(EC.presence_of_element_located((By.ID, "idSpanClasseDescricao")))
        classe_texto = classe_span.text.strip()
        numero_processo = classe_texto.replace("HC nº", "").strip() if classe_texto.startswith("HC nº") else classe_texto

        # Relator(a)
        spans = driver.find_elements(By.CLASS_NAME, "classSpanDetalhesLabel")
        relator = "Não localizado"
        situacao = "Não localizada"
        data_autuacao = "Não localizada"

        for i, span in enumerate(spans):
            texto_label = span.text.upper().strip()
            if "RELATOR" in texto_label:
                try:
                    relator_span = spans[i].find_element(By.XPATH, "following-sibling::span[@class='classSpanDetalhesTexto']")
                    relator = relator_span.text.strip()
                except:
                    relator = "Erro ao localizar"
            elif "AUTUAÇÃO" in texto_label:
                try:
                    autuacao_span = spans[i].find_element(By.XPATH, "following-sibling::span[@class='classSpanDetalhesTexto']")
                    data_autuacao = autuacao_span.text.strip()
                except:
                    data_autuacao = "Erro ao localizar"

        # Situação atual
        situacao_spans = driver.find_elements(By.CLASS_NAME, "classSpanDetalhesTexto")
        for span in situacao_spans:
            texto = span.text.strip()
            if any(palavra in texto for palavra in ["CONCLUSOS", "AGUARDANDO", "VISTA", "JULGAMENTO", "PROFERIDA"]):
                situacao = texto
                break

        # Número CNJ
        try:
            numero_unico_link = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'tipoPesquisaNumeroUnico')]"))
            )
            numero_cnj = numero_unico_link.text.strip()
        except:
            numero_cnj = "Não localizado"

        return {
            "numero_cnj": numero_cnj,
            "numero_processo": numero_processo,
            "relator": relator,
            "situacao": situacao,
            "data_autuacao": data_autuacao
        }

    except Exception as e:
        print(f"⚠️ Erro ao extrair dados de {titulo}: {e}")
        return None
