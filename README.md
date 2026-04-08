# DanviciRPC

Discord Rich Presence para DaVinci Resolve usando Python, exibindo em tempo real o modo de edição ativo, o nome do projeto e o tempo de sessão contínuo.

---

## ✨ Funcionalidades

- Detecta automaticamente o processo do DaVinci Resolve (Windows e Linux)
- Identifica o modo de edição ativo (Cut, Edit, Color Grading, Fusion, Audio) via título da janela
- Exibe nome do projeto e timeline via a API de scripting do Resolve (opcional)
- Tempo de sessão contínuo — **não reinicia** a cada atualização do loop
- Reconexão automática com Discord com backoff exponencial
- Fallback automático quando o Resolve não está disponível ou a API não responde
- Zero crashes — todos os pontos de falha são tratados com logging estruturado

---

## 🏗️ Estrutura do Projeto

```
DanviciRPC/
├── main.py               # Orquestração principal
├── config.py             # Configurações (CLIENT_ID, intervalos, flags)
├── logger.py             # Logging estruturado
├── requirements.txt
├── core/
│   ├── session.py        # SessionTracker — controle de tempo de sessão
│   └── state_manager.py  # StateManager — estado centralizado da aplicação
├── resolve/
│   ├── detector.py       # Detecção de processo e modo via janela
│   └── resolver.py       # Integração com DaVinciResolveScript API
└── discord/
    └── rpc_client.py     # Cliente Discord RPC (pypresence)
```

---

## ⚙️ Configuração

### 1. Obter o Client ID do Discord

1. Acesse o [Discord Developer Portal](https://discord.com/developers/applications).
2. Crie uma nova aplicação (ex.: `DaVinci Resolve`).
3. Copie o **Application ID** exibido na página "General Information".
4. Na aba **Rich Presence → Art Assets**, faça o upload de um asset com o nome `resolve` (ou ajuste `LARGE_IMAGE_KEY` em `config.py`).

### 2. Definir o CLIENT_ID

A forma recomendada é via variável de ambiente (sem colocar segredos no código):

```bash
export DISCORD_CLIENT_ID="SeuClientIdAqui"
```

Ou edite `config.py` e substitua o valor padrão:

```python
CLIENT_ID: str = os.environ.get("DISCORD_CLIENT_ID", "SeuClientIdAqui")
```

### 3. Outras opções (variáveis de ambiente)

| Variável              | Padrão  | Descrição                                             |
|-----------------------|---------|-------------------------------------------------------|
| `DISCORD_CLIENT_ID`   | —       | **Obrigatório** — ID da aplicação Discord             |
| `UPDATE_INTERVAL`     | `15`    | Intervalo de atualização do RPC em segundos           |
| `ENABLE_RESOLVE_API`  | `true`  | Ativa a integração com a API de scripting do Resolve  |

---

## 🔐 Secrets no GitHub

Configure os seguintes secrets no repositório (**Settings → Secrets and variables → Actions → New repository secret**):

| Secret              | Descrição                                                   |
|---------------------|-------------------------------------------------------------|
| `DISCORD_CLIENT_ID` | Application ID do Discord Developer Portal                  |
| `LARGE_IMAGE_KEY`   | Nome do asset de imagem registrado no Discord (ex.: `resolve`) |

O pipeline injeta esses valores como variáveis de ambiente no momento do build. O binário gerado **lê esses valores em tempo de execução** — nunca ficam embutidos no código.

---

## 🔄 Pipeline CI/CD

O arquivo `.github/workflows/release.yml` executa automaticamente a cada push na branch `main`:

1. **Build matrix** (paralelo em 3 plataformas):
   - `windows-latest` → gera `resolve-rpc-windows.exe`
   - `ubuntu-latest` → gera `resolve-rpc-linux.deb`
   - `macos-latest` → gera `resolve-rpc-macos.dmg`
2. **Release automático**: cria uma release no GitHub com os três artefatos anexados e tag no formato `v{YYYY.MM.DD}-build-{N}`.

O build usa **PyInstaller** (`resolve-rpc.spec`) para gerar executáveis standalone — sem necessidade de Python instalado na máquina do usuário final.

---

## 🛠️ Build Local

Para gerar o executável na sua máquina:

```bash
# Instalar dependências + PyInstaller
pip install -r requirements.txt pyinstaller

# Gerar binário
pyinstaller resolve-rpc.spec
```

O executável ficará em `dist/resolve-rpc` (Linux/macOS) ou `dist/resolve-rpc.exe` (Windows).

---



### Pré-requisitos

- Python 3.10+
- DaVinci Resolve instalado (opcional para testes sem API)
- Discord rodando em segundo plano

### Instalação

```bash
pip install -r requirements.txt
```

### Execução

```bash
python main.py
```

Para parar, pressione `Ctrl+C` — o programa encerrará de forma limpa.

---

## ⚠️ Limitações do Resolve

- A **API de scripting** (`DaVinciResolveScript`) só está disponível quando o DaVinci Resolve está aberto e configurado para aceitar conexões externas. Caso contrário, o sistema opera em modo heurístico (detecção via janela).
- No **Linux**, a detecção de janela via `pygetwindow` pode não funcionar em ambientes sem servidor de exibição (headless). O modo de edição será reportado como `"Idle"` nesses casos.
- No **macOS**, `pygetwindow` tem suporte limitado; a detecção de modo pode ser menos precisa.
- O asset de imagem `resolve` precisa estar cadastrado no Discord Developer Portal para aparecer corretamente na presença.
