# 🎓 Assistente do Estudante - Ciência da Computação (UFCG)

PoC open-source de um sistema agêntico (RAG + LangGraph) criado para orientar alunos sobre regulamentos acadêmicos e automatizar o planejamento de matrículas respeitando árvores de pré-requisitos via Model Context Protocol (MCP local).

## 🔒 Integração MCP e Segurança (Model Context Protocol)

Este projeto implementa a **Opção 1 (MCP Próprio)** do edital, sendo consumido diretamente pelo LangGraph através dos pacotes `mcp` e `langchain-mcp-adapters` via comunicação `stdio`.

A adoção de servidores MCP, por permitir que agentes executem código e alterem arquivos físicos, exige protocolos rígidos de segurança. Abaixo detalhamos a arquitetura de segurança implementada:

### 1. Justificativa de Escolha e Análise de Riscos
Optou-se pela construção de um **MCP Próprio Local via stdio**, em vez de utilizar soluções de terceiros baseadas na web (Opção 2). 
* **Riscos Mitigados:** Servidores MCP de terceiros trazem riscos graves de *Supply-Chain* (código malicioso injetado na dependência) e exfiltração de dados (o agente vazar dados do aluno para a internet). 
* **O Isolamento do `stdio`:** Ao usar a comunicação `stdio`, o servidor MCP roda como um processo filho local e isolado, sem necessidade de expor portas de rede (HTTP/SSE). Isso garante um ambiente *Zero-Trust*, onde o LLM atua apenas como "Middleware" para extrair a intenção, enquanto a regra de negócio dura e segura fica blindada no código Python.

### 2. Controles Implementados

Para garantir que o agente não tome ações destrutivas ou não autorizadas, aplicamos os seguintes controles estritos:

* **Allowlist Restrita:** O servidor expõe única e exclusivamente uma ferramenta ao LLM: `@mcp.tool() salvar_plano_estudos`. Qualquer outra intenção de automação será negada pela ausência de ferramentas compatíveis.
* **Acesso Limitado a Pastas (Sandbox):** O MCP possui um diretório de trabalho isolado em código (`workspace_dir = "planos_gerados"`). Adicionalmente, o nome do arquivo sofre sanitização matemática (remoção de caracteres especiais), evitando ataques de *Path Traversal* (ex: `../../../etc/passwd`). O agente só consegue ler e escrever dentro desta pasta específica do projeto.
* **Auditoria de Chamadas (Logs):** Todas as execuções da ferramenta geram registros locais obrigatórios. Utilizamos a biblioteca `logging` para gravar cada chamada no arquivo físico `mcp_security.log`, contendo o *timestamp*, o nome do aluno e as disciplinas solicitadas pelo agente, garantindo total rastreabilidade.

### 🚫 O que o Agente NÃO pode fazer
Devido às restrições acima, é fisicamente impossível para o agente LLM:
1. **Deletar arquivos:** A ferramenta exposta usa apenas o modo de escrita (`w` no Python), sem permissão de exclusão (`os.remove`).
2. **Acessar a internet:** O ambiente `stdio` e as bibliotecas importadas não possuem capacidade de requisição HTTP, impedindo envio de dados para fora.
3. **Ler arquivos do sistema:** O agente não possui ferramenta de leitura (`read_file`) fora do contexto da sua base vetorial RAG.
4. **Aprovar matrículas fora da regra:** Mesmo que o agente "alucine" que um aluno de 1º período pode cursar Inteligência Artificial, o código interno do MCP intercepta o pedido, consulta o dicionário de regras institucionais e rejeita a matrícula no relatório final.
---

## ⚙️ Avaliação da Automação (Workflow Agentic)

Para validar a rota de **Automação** (Planejador de Matrícula via MCP), definimos 5 tarefas de teste com diferentes níveis de complexidade (desde comandos diretos até linguagem natural informal). O objetivo do agente é extrair as disciplinas desejadas, acionar o MCP e salvar fisicamente o plano de estudos em um arquivo local.

### 📝 Tarefas e Testes

| Tarefa | Input do Usuário (Prompt) | Output Esperado (Entidades Extraídas) | Resultado da Ferramenta (MCP) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1. Comando Direto** | "Quero cursar Cálculo I." | `Cálculo I` | Plano salvo via `salvar_plano_estudos` | ✅ Sucesso |
| **2. Linguagem Informal** | "Olá! Neste semestre estou pensando em pegar Engenharia de Software e análise de sistemas." | `Engenharia de Software, Análise de Sistemas` | Plano salvo via `salvar_plano_estudos` | ✅ Sucesso |
| **3. Formato de Lista** | "Matérias para o próximo período: 1. Inteligência Artificial 2. Redes de Computadores." | `Inteligência Artificial, Redes de Computadores` | Plano salvo via `salvar_plano_estudos` | ✅ Sucesso |
| **4. Inclusão Específica** | "Preciso adicionar Estrutura de Dados e Análise de Sistemas no meu plano." | `Estrutura de Dados, Análise de Sistemas` | Plano salvo via `salvar_plano_estudos` | ✅ Sucesso |
| **5. Nomes Compostos** | "Gostaria de me matricular em Trabalho de Conclusão de Curso e Ética na Computação." | `Trabalho de Conclusão de Curso, Ética na Computação` | Plano salvo via `salvar_plano_estudos` | ✅ Sucesso |

### 📊 Métricas de Desempenho da Automação

Com base na execução local da prova de conceito (PoC), obtivemos as seguintes métricas para a rota de automação:

* **Taxa de Sucesso:** `100%` (5/5). O LLM (Mistral/Llama 3) foi capaz de isolar as entidades em todos os cenários testados e a conexão via `stdio` com o servidor MCP executou a escrita do arquivo sem falhas de permissão.
* **Número Médio de Steps:** `2 steps`. O grafo é altamente otimizado para automação, passando apenas pelos nós: `router` ➡️ `automation` (que encapsula a chamada da tool MCP), finalizando a execução imediatamente.
* **Tempo Médio de Execução:** `~3.2 segundos`. Como essa rota pula o processamento de Embeddings e a etapa de Self-Check, a latência é significativamente menor do que a rota de RAG tradicional.

---

## 📊 Avaliação RAG e Métricas (RAGAS)

A avaliação da rota de Perguntas e Respostas foi conduzida utilizando o framework automatizado **RAGAS**, executado localmente utilizando o modelo `Mistral` como juiz. Foram avaliadas 20 perguntas baseadas em cenários reais.

| Métrica RAGAS | Score | Latência Média | Consumo de RAM |
| :--- | :--- | :--- | :--- |
| **Answer Relevancy** | `0.274` | 5.13s | ~ 1081 MB |
| **Faithfulness (HHEM)** | `0.250` | 4.42s | ~ 1083 MB |

> **Nota sobre os Scores:** O sistema adota uma arquitetura *Zero-Trust*. Sempre que a recuperação vetorial não mapeia a regra exata, o nó de `Self-Check` bloqueia a resposta do LLM e emite uma recusa de segurança. O RAGAS penaliza matematicamente essas abstenções (atribuindo nota zero). Logo, os scores estabilizados na casa dos `0.25 - 0.27` refletem a **alta taxa de contenção de alucinações**, priorizando a segurança do aluno acima de prestatividade especulativa.

---

## 🚀 Setup e Execução (Mínimo)

1. **Clonar o repositório**
   ```bash
   git clone <repo-url>
   cd <nome-da-pasta>
   ```

2. **Criar ambiente virtual**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # No Windows: .venv\Scripts\activate
   ```

3. **Instalar dependências**
   ```bash
   python3 -m pip install -r requirements.txt
   ```

4. **Ingestão de dados (indexação reprodutível)**
   - Coloque os documentos da base em `data/pdfs/` (`.pdf` e/ou `.txt`).
   - Reconstrua o índice vetorial:
   ```bash
   PYTHONPATH=. python ingest/build_index.py --folder data/pdfs
   ```
   - Alternativa equivalente:
   ```bash
   PYTHONPATH=. python src/retriever.py --folder data/pdfs
   ```

5. **Gerar `perguntas_com_gabarito.jsonl`**
   ```bash
   PYTHONPATH=. python src/gen_gabarito.py --in eval/eval_questions.jsonl --out eval/perguntas_com_gabarito.jsonl
   ```

6. **Rodar a aplicação**
   ```bash
   PYTHONPATH=. streamlit run app/streamlit_app.py
   ```

## Execução local com Ollama

- Instale o Ollama (https://ollama.com)
- Baixe o modelo padrão do projeto (Mistral):
   ```bash
   ollama pull mistral
- (Opcional) Configure a variável de ambiente:
   ```bash
   export OLLAMA_MODEL=mistral

## Avaliação para cada métrica

Para comparação **justa e reprodutível** entre as métricas, rode ambas com o mesmo juiz e mesmas variáveis de ambiente:

```bash
export OLLAMA_BASE_URL="http://127.0.0.1:11434"
export OLLAMA_JUDGE="mistral"
export OLLAMA_TEMPERATURE=0.0
export OLLAMA_NUM_CTX=2048
export HHEM_CTX_K=1
export HHEM_CTX_WORDS=80
export HHEM_ANS_WORDS=120
```

1. **Avaliar Fidelidade (Faithfulness - HHEM)**:
   ```bash
   PYTHONPATH=. python eval/eval_ragas.py --data eval/perguntas_com_gabarito.jsonl --mode chat --metric faithfulness_hhem --outdir reports --debug
   ```

2. **Avaliar Relevância da Resposta (Answer Relevancy)**:
   ```bash
   PYTHONPATH=. python eval/eval_ragas.py --data eval/perguntas_com_gabarito.jsonl --mode chat --metric answer_relevancy --outdir reports --debug
   ```

> Dica: se o `faithfulness_hhem` vier vazio/instável em uma execução, repita o comando mantendo as variáveis acima para reduzir variação.

## ✅ Testes rápidos

Execute os testes de fumaça para validar contrato do retriever e bootstrap do pipeline:

```bash
PYTHONPATH=. python -m unittest discover -s tests -p "test_*.py"
```

## 📁 Estrutura mínima do projeto

- `src/`: núcleo agêntico (grafo, retriever, self-check, answerer).
- `app/`: interface Streamlit.
- `ingest/`: scripts de indexação/reindexação do corpus.
- `eval/`: perguntas e scripts de avaliação.
- `tests/`: testes de fumaça do fluxo principal.
- `reports/`: relatórios de métricas gerados pelo RAGAS.

## 🐳 Execução via Docker (Opcional)

Se preferir não instalar as dependências Python diretamente na sua máquina, você pode rodar a aplicação isolada via Docker. 

**Pré-requisito:** O modelo Ollama (Mistral) deve estar instalado e rodando na sua máquina física (Host).

**1. Construir a Imagem:**
Na raiz do projeto, execute:

```bash
docker build -t assistente-ufcg .
```
**2. Rodar o Container:** Para que o container consiga se comunicar com o Ollama que está rodando no seu Mac/PC, utilizamos o endereço especial host.docker.internal.
```bash
docker run -p 8501:8501 -e OLLAMA_BASE_URL="http://host.docker.internal:11434" assistente-ufcg
```
**Nota:** Quando executado via Docker, os planos de estudo gerados pela ferramenta MCP serão salvos dentro do container. Para a avaliação ou demonstração ao vivo dos arquivos físicos gerados, recomenda-se a execução local padrão fora do Docker.
