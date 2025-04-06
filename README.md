# Scraper de HCs no STJ (Origem TJGO) ⚖️➡️📊

Este projeto automatiza a busca por **Habeas Corpus (HCs)** no site do Superior Tribunal de Justiça (STJ), especificamente aqueles com **origem no Tribunal de Justiça de Goiás (TJGO)**. Os resultados encontrados são extraídos, processados e exportados para uma planilha Excel (`.xlsx`). A execução pode ser manual ou agendada automaticamente via GitHub Actions, com envio de um relatório por e-mail.

---

## ✨ Como Funciona

1.  **Acesso e Pesquisa:** O script utiliza Selenium para controlar um navegador Chrome (em modo headless no GitHub Actions) e acessar a página de pesquisa avançada do STJ.
2.  **Preenchimento:** As datas desejadas (ou a data de ontem, por padrão) e o órgão de origem (TJGO) são inseridos no formulário.
3.  **Navegação e Extração:** O script navega pelas páginas de resultados, identifica os links de HCs e abre cada um em uma nova aba para extrair detalhes como número CNJ, relator(a) e situação atual.
4.  **Exportação:** Se HCs forem encontrados, seus detalhes são compilados e salvos em um arquivo `.xlsx` na pasta do projeto (ou no ambiente do runner do GitHub Actions).
5.  **Status (GitHub Actions):** Ao final da execução via Actions, um arquivo `info_execucao.json` é gerado contendo um resumo (datas, contagens, erros, etc.).
6.  **Notificação (GitHub Actions):** O workflow lê o `info_execucao.json`, monta um e-mail de status (informando sucesso com/sem HCs ou erros) e o envia para o destinatário configurado, anexando o arquivo `.xlsx` se ele foi gerado com sucesso.

---

## ⚙️ Requisitos

**Para execução local:**

*   Python 3.10+
*   Git
*   Gerenciador de pacotes `pip`
*   Google Chrome instalado
*   Dependências Python listadas em `requirements.txt` (instaladas via `pip`)

**Para execução via GitHub Actions:**

*   Nenhuma instalação local necessária. O ambiente é configurado pelo workflow.
*   Configuração dos `Secrets` no repositório GitHub (veja a seção Configuração).

---

## 🔧 Instalação (Local)

1.  Clone o repositório:
    ```bash
    git clone https://github.com/guszzpp/scraperstjhc.git
    cd scraperstjhc
    ```

2.  Crie e ative um ambiente virtual (recomendado):
    ```bash
    python -m venv venv
    # No Windows:
    # venv\Scripts\activate
    # No Linux/macOS:
    # source venv/bin/activate
    ```

3.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

---

## 🛠️ Configuração (GitHub Actions)

Para que o envio automático de e-mails via GitHub Actions funcione, você precisa configurar os seguintes **Secrets** no seu repositório (Vá para `Settings` > `Secrets and variables` > `Actions` > `New repository secret`):

*   `EMAIL_USUARIO`: O endereço de e-mail que será usado para enviar o relatório (ex: `seu_email@gmail.com`).
*   `EMAIL_SENHA`: A senha de aplicativo específica para o e-mail configurado (❗️**Importante:** Para Gmail, você provavelmente precisará gerar uma "Senha de App" - não use sua senha principal do Google. Veja a [documentação do Google sobre Senhas de App](https://support.google.com/accounts/answer/185833)).
*   `EMAIL_DESTINATARIO`: O endereço de e-mail que receberá o relatório.

---

## ▶️ Execução

**Execução Manual (Local):**

Execute o script principal a partir da pasta raiz do projeto.

*   **Usando a data de ontem (padrão):**
    ```bash
    python main.py
    ```

*   **Especificando uma data única (será usada como data inicial e final):**
    ```bash
    python main.py DD/MM/AAAA
    # Exemplo: python main.py 25/12/2023
    ```

*   **Especificando um intervalo de datas:**
    ```bash
    python main.py DD/MM/AAAA_inicial DD/MM/AAAA_final
    # Exemplo: python main.py 01/01/2024 31/01/2024
    ```

**Execução Automática (GitHub Actions):**

*   O workflow definido em `.github/workflows/rodar_scraper.yml` é configurado para rodar automaticamente todos os dias às **11:00 (horário de Brasília - UTC-3)**, correspondente a `cron: '0 14 * * *'` (14:00 UTC).
*   Ele também pode ser acionado manualmente na aba "Actions" do seu repositório no GitHub.

---

## 📊 Saída

**Arquivo Excel (.xlsx):**

*   Se HCs forem encontrados durante a execução (manual ou automática), um arquivo Excel será gerado.
*   **Nome:**
    *   Data única: `hc_tjgo_DD-MM-AAAA.xlsx`
    *   Intervalo: `hc_tjgo_DD-MM-AAAA_inicial_a_DD-MM-AAAA_final.xlsx`
*   **Localização:**
    *   Execução Local: Na mesma pasta onde você executou `python main.py`.
    *   GitHub Actions: O arquivo é gerado no ambiente do runner e anexado ao e-mail de notificação (se houver HCs e nenhum erro crítico).
*   **Conteúdo:** Contém colunas como Número CNJ, Número do Processo, Relator(a), Situação e Data de Autuação (aproximada).

**E-mail de Notificação (via GitHub Actions):**

Um e-mail será enviado ao `EMAIL_DESTINATARIO` após cada execução agendada ou manual via Actions, informando:

*   **Status Geral:** Sucesso com HCs, Sucesso sem HCs, Erro interno do script, ou Falha na execução do script.
*   **Detalhes da Execução:** Período de busca, órgão de origem (TJGO), quantos resultados o site reportou, quantos HCs foram efetivamente extraídos, quantas páginas foram processadas, horário de finalização e duração.
*   **Anexo:** O arquivo `.xlsx` será anexado se a execução foi bem-sucedida e HCs foram encontrados.
*   **Mensagem de Erro:** Se ocorrer um erro, a mensagem de erro será incluída no corpo do e-mail.
*   **Link para a Execução:** Um link direto para a página da execução no GitHub Actions para consulta de logs.
*   **Alerta:** Um lembrete de que a automação é um auxílio e não substitui a conferência manual.

---

## 📁 Estrutura do Projeto
.
├── .github/
│ └── workflows/
│ └── rodar_scraper.yml # Define o workflow do GitHub Actions
├── config.py # Configurações (URL, Órgão, Datas padrão)
├── exportador.py # Lógica para criar o arquivo .xlsx
├── extrator.py # Lógica para extrair dados da página de detalhes do HC
├── formulario.py # Lógica para preencher o formulário de pesquisa
├── main.py # Ponto de entrada, orquestra o fluxo principal
├── navegador.py # Configuração e inicialização do Selenium WebDriver
├── paginador.py # Lógica para navegar entre páginas de resultados
├── requirements.txt # Lista de dependências Python
└── README.md # Este arquivo


*(Nota: O arquivo `info_execucao.json` é gerado durante a execução do `main.py` e usado pelo workflow, mas geralmente não é versionado).*
