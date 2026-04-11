<p align="center">
  <img src="https://github.com/user-attachments/assets/b052d5f9-18aa-46f9-ae59-ee4131f28a3d" width="200" alt="DaVinciRPC Logo" />
</p>

<h1 align="center">DaVinciRPC</h1>

<p align="center">
  <img src="https://img.shields.io/github/v/release/Polabiel/DaVinciRPC?style=for-the-badge&color=6366f1" alt="Release" />
  <img src="https://img.shields.io/github/license/Polabiel/DaVinciRPC?style=for-the-badge" alt="License" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python" alt="Python Version" />
  <img src="https://img.shields.io/badge/Discord-RPC-5865F2?style=for-the-badge&logo=discord" alt="Discord RPC" />
</p>

<p align="center">
  <strong>Leve o status do seu workflow de edição para o próximo nível.</strong><br />
  Uma integração elegante entre DaVinci Resolve e Discord escrita em Python.
</p>

---

## 🚀 O que é o DaVinciRPC?

O **DaVinciRPC** monitora sua atividade no DaVinci Resolve e a exibe em tempo real no seu perfil do Discord. Seja você um colorista, editor ou artista de Fusion, seus amigos saberão exatamente em que etapa do projeto você está trabalhando.

### ✨ Destaques
* **Inteligência Multiplataforma:** Suporte nativo para Windows e Linux.
* **Detecção de Contexto:** Identifica os modos `Cut`, `Edit`, `Color`, `Fusion` e `Fairlight`.
* **Tempo de Sessão Persistente:** O cronômetro não zera se o script oscilar.
* **Resiliência:** Reconexão automática com backoff exponencial e tratamento de exceções robusto.

---

## 📂 Estrutura do Projeto

A arquitetura foi desenhada para ser modular e fácil de manter:

```text
📦 DaVinciRPC
 ┣ 📂 core          # Gerenciamento de estado e rastreio de sessão
 ┣ 📂 discord       # Comunicação com a API do Discord (pypresence)
 ┣ 📂 resolve       # Lógica de detecção de janelas e scripts do Resolve
 ┣ 📜 main.py       # Ponto de entrada da aplicação
 ┗ 📜 config.py     # Central de variáveis e ambiente
```

---

## ⚙️ Configuração Rápida

### 1. Preparando o Discord
1. Vá ao [Discord Developer Portal](https://discord.com/developers/applications).
2. Crie uma aplicação chamada `DaVinci Resolve`.
3. Em **Rich Presence > Art Assets**, suba uma imagem com a chave `resolve`.

### 2. Variáveis de Ambiente
Recomendamos o uso de um arquivo `.env` na raiz do projeto para manter suas credenciais seguras:

| Variável | Descrição |
| :--- | :--- |
| `DISCORD_CLIENT_ID` | O ID da sua aplicação no Discord. |
| `LARGE_IMAGE_KEY` | Nome do asset de imagem (ex: `resolve`). |
| `ENABLE_RESOLVE_API` | `true` para usar a API de scripting oficial. |

---

## 🛠️ Instalação e Uso

### Modo Desenvolvedor
```bash
# Clone o repositório
git clone [https://github.com/Polabiel/DaVinciRPC.git](https://github.com/Polabiel/DaVinciRPC.git)

# Instale as dependências
pip install -r requirements.txt

# Inicie o tracker
python main.py
```

### Build de Produção
Se quiser gerar um executável (.exe ou binário Linux) sem depender do Python instalado:
```bash
pip install pyinstaller
pyinstaller resolve-rpc.spec
```

---

## 🔄 Pipeline CI/CD

Este projeto utiliza **GitHub Actions** para automação total. A cada novo *push* na branch `main`:
1. O código é testado.
2. Binários para **Windows, Linux e macOS** são gerados via PyInstaller.
3. Uma nova **Release** é criada automaticamente com os arquivos prontos para uso.

---

## ⚠️ Notas de Compatibilidade

> [!IMPORTANT]
> A API de Scripting do DaVinci Resolve geralmente requer a versão **Studio**. Para usuários da versão gratuita, o DaVinciRPC utiliza **Heurística de Janelas** para detectar o modo de edição, garantindo funcionalidade básica para todos.

* **Linux:** Requer ambiente X11 para detecção de janelas.
* **macOS:** Suporte em fase experimental (detecção de janelas limitada).

---

<p align="center">
  Desenvolvido com 💙 por <a href="https://github.com/Polabiel">Polabiel</a>
</p>
