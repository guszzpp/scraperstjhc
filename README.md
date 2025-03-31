# Scraper STJ HC

Este projeto é um scraper automatizado para coletar processos de Habeas Corpus (HC) no site do Superior Tribunal de Justiça (STJ). Utiliza a biblioteca Selenium para interagir com a interface do site, extrair dados relevantes e gerar um relatório diário em formato Excel (`.xlsx`).

## 🔍 Funcionalidades

- Preenchimento automático dos filtros de pesquisa no site do STJ.
- Busca diária de processos de Habeas Corpus (HC) **provenientes do TJGO**.
- Extração automática dos seguintes dados:
  - Número CNJ (número único)
  - Número do processo (ex: HC 992215 / GO)
  - Nome do relator(a)
  - Situação atual do processo
  - Data de autuação
- Navegação por todas as páginas de resultados.
- Geração de planilha Excel com os resultados encontrados.
- Execução automatizada diária via **GitHub Actions** às 00:00.
- Envio automático do arquivo `.xlsx` por **e-mail** ao final da execução.

## ✅ Requisitos

- Python 3.8 ou superior
- Google Chrome (última versão)
- [ChromeDriver](https://sites.google.com/chromium.org/driver/) (gerenciado automaticamente por `webdriver_manager`)
- Conta no GitHub (para agendamento automático)
- Variáveis de ambiente configuradas no GitHub Secrets (para envio por e-mail)

## 🚀 Instalação e Uso Local

1. Clone o repositório:

   ```bash
   git clone https://github.com/seu-usuario/scraperstjhc.git
   cd scraperstjhc