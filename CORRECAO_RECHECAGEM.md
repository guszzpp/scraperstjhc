# 🔧 Correção do Sistema de Rechecagem

## ❌ Problemas Identificados

### 1. **Lógica de Rechecagem Incorreta**
- O código original tentava baixar arquivos do Supabase em vez de usar arquivos locais
- Caminhos inconsistentes: procurava em `dados_hoje/` que não existe
- Não seguia o fluxo correto D+1 vs D+2

### 2. **Fluxo Incorreto**
- **Como deveria ser**: D+1 (primeira raspagem) → D+2 (segunda raspagem + comparação)
- **Como estava**: Tentava comparar com arquivos do Supabase que podem não existir

### 3. **Falta de Integração**
- O `main.py` não chamava a rechecagem automaticamente
- A rechecagem precisava ser executada manualmente

## ✅ Correções Implementadas

### 1. **Nova Lógica de Rechecagem** (`retroativos/rechecagem.py`)
```python
# ANTES: Tentava baixar do Supabase
download_from_supabase(...)

# DEPOIS: Usa arquivos locais
arquivo_d1_xlsx = f"dados_diarios/hc_tjgo_{nome_data_d1}.xlsx"
arquivo_d2_xlsx = f"dados_diarios/hc_tjgo_{nome_data}.xlsx"
```

### 2. **Fluxo Correto D+1 vs D+2**
- **D+1**: Primeira raspagem (salva em `dados_diarios/`)
- **D+2**: Segunda raspagem + comparação com D+1
- Identifica novos HCs que apareceram em D+2 mas não em D+1

### 3. **Executor Automático** (`retroativos/executor_rechecagem.py`)
- Verifica automaticamente se existem arquivos D+1 e D+2
- Executa rechecagem quando apropriado
- Pode ser executado manualmente ou automaticamente

## 🚀 Como Usar

### Execução Automática
```bash
python retroativos/executor_rechecagem.py
```

### Execução Manual
```bash
python retroativos/executor_rechecagem.py DD/MM/AAAA
```

### Teste da Rechecagem
```bash
python teste_rechecagem.py
```

## 📊 Fluxo Correto

1. **Dia 1**: Executar `python main.py DD/MM/AAAA` (primeira raspagem)
2. **Dia 2**: Executar `python main.py DD/MM/AAAA` (segunda raspagem)
3. **Dia 2**: Executar `python retroativos/executor_rechecagem.py` (rechecagem)

## 🔍 O que a Rechecagem Detecta

- **Novos HCs**: Presentes em D+2 mas não em D+1
- **HCs Removidos**: Presentes em D+1 mas não em D+2
- **Alterações**: Mudanças em campos de HCs existentes

## 📧 Saídas

- `novos_retroativos.xlsx`: HCs retroativos detectados
- `email_subject.txt`: Assunto do e-mail
- `email_body.txt`: Corpo do e-mail
- `attachment.txt`: Caminho do anexo

## ⚠️ Importante

- A rechecagem só funciona se existirem arquivos de D+1 e D+2
- Execute primeiro as raspagens antes da rechecagem
- A data passada para rechecagem deve ser D+2 (quando a rechecagem é executada)
