# Scraper de HCs no STJ (origem TJGO)

Este projeto realiza buscas automáticas no site do Superior Tribunal de Justiça (STJ), filtrando apenas **Habeas Corpus** com **origem no Tribunal de Justiça de Goiás - TJGO**, e exporta os dados relevantes para planilha Excel (.xlsx).

---

## ⚙️ Requisitos

- Python 3.10+
- Google Chrome instalado
- ChromeDriver compatível (gerenciado automaticamente com `webdriver_manager`)
- Conta de e-mail configurada no GitHub Secrets, se desejar envio automático

---

## 🔧 Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Execução manual

Você pode executar o script com:

- Sem argumentos (usa ontem):
  ```bash
  python main.py
  ```

- Uma data específica (usa como início e fim):
  ```bash
  python main.py 28/03/2025
  ```

- Um intervalo de datas:
  ```bash
  python main.py 01/03/2025 31/03/2025
  ```

---

## 📬 Exportação

Se houver resultados, será gerado automaticamente um arquivo `.xlsx` com os dados extraídos. O nome do arquivo será:

- Para data única:
  ```
  hc_tjgo_dd-mm-aaaa.xlsx
  ```

- Para intervalo de datas:
  ```
  hc_tjgo_dd-mm-aaaa_a_dd-mm-aaaa.xlsx
  ```

---

## 🔁 Agendamento automático (GitHub Actions)

O script é executado automaticamente todos os dias às **12:00 (horário de Brasília)**.

---

## 📧 Envio de e-mail

O corpo da mensagem enviada pelo GitHub Actions incluirá:

- Datas de busca
- Total de processos retornados
- Quantos são Habeas Corpus (HCs)
- Quantidade de páginas analisadas
- Horário de finalização
- Alerta sobre a necessidade de conferência manual

---

## 📁 Estrutura

- `main.py`: fluxo principal
- `formulario.py`: preenchimento do formulário
- `paginador.py`: controle de páginas
- `extrator.py`: extração dos dados do processo
- `exportador.py`: exportação para Excel
- `email_detalhado.py`: corpo do e-mail gerado
- `config.py`: configurações básicas
- `.github/workflows/main.yml`: agendamento automático

---

## 🔒 Segurança

As credenciais para envio de e-mail são lidas dos `Secrets` configurados no repositório do GitHub:

- `EMAIL_USUARIO`
- `EMAIL_SENHA`
- `EMAIL_DESTINATARIO`

---

## 📄 Licença

MIT License.
