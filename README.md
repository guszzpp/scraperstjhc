# Scraper STJ - Habeas Corpus (HC) com origem no TJGO

Este projeto automatiza a coleta diária de dados sobre Habeas Corpus (HC) autuados no site do Superior Tribunal de Justiça (STJ), com origem no Tribunal de Justiça de Goiás (TJGO). Os dados coletados incluem:

    Número do processo (formato STJ)

    Número único CNJ

    Relator(a)

    Situação atual

    Data da autuação

# 📁 Estrutura modular

scraperstjhc/
├── main.py                 # Script principal (orquestra tudo)
├── config.py              # Configurações de data e parâmetros
├── navegador.py           # Inicialização do navegador
├── extrator.py            # Extração de dados da página de cada processo
├── exportador.py          # Exportação dos dados para planilha .xlsx
├── requirements.txt       # Dependências do projeto
└── .github/workflows/     # (opcional) Automação via GitHub Actions

# ⚙️ Requisitos

    Python 3.8 ou superior

    Google Chrome instalado

    Ambiente virtual ativo (recomendado)

# 🚀 Instalação

Abra um terminal e execute:

1. Clone o repositório
git clone https://github.com/seu-usuario/scraperstjhc.git
cd scraperstjhc

2. Crie o ambiente virtual
python -m venv venv

3. Ative o ambiente virtual
- No Windows:
venv\Scripts\activate
- No Linux/Mac:
source venv/bin/activate

4. Instale as dependências
pip install -r requirements.txt

# ▶️ Execução manual

Por padrão, o script busca os HCs autuados ontem:

python main.py

Você também pode passar uma data específica no formato dd/mm/aaaa:

python main.py 28/03/2025

# 📬 Exportação

Se houver resultados, será gerado automaticamente um arquivo .xlsx com nome no formato:

hc_tjgo_30-03-2025.xlsx

# 🔁 Agendamento automático (GitHub Actions)

Este projeto pode ser automatizado via GitHub Actions. O workflow:

    Executa todos os dias às 00:00 (horário de Brasília)

    Busca os HCs com base na data do dia anterior

    Exporta os dados

    Envia o arquivo por e-mail (se os GitHub Secrets estiverem configurados)

    ⚠️ Certifique-se de configurar corretamente os segredos no repositório para o envio de e-mails automáticos funcionar.

# 🔒 Segurança

Este projeto não armazena senhas nem dados sensíveis no código-fonte. As credenciais para envio de e-mail são armazenadas com segurança no GitHub como secrets.

# 📄 Licença

Este projeto está licenciado sob os termos da Licença MIT.