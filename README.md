# Assistente do Estudante - Ciência da Computação (UFCG)

PoC open-source de um sistema agêntico (RAG + LangGraph) criado para orientar alunos sobre regulamentos acadêmicos e automatizar o planejamento de matrículas respeitando árvores de pré-requisitos via Model Context Protocol (MCP local).

## 🔒 Integração MCP e Segurança (Model Context Protocol)

Este projeto implementa a **Opção 1 (MCP Próprio)**, consumido diretamente pelo LangGraph através dos pacotes `mcp` e `langchain-mcp-adapters` via comunicação `stdio`.

Para mitigar os riscos inerentes de segurança em servidores MCP (como exfiltração de dados e Supply-Chain), as seguintes diretrizes foram implementadas no `mcp_server.py`:

* **Allowlist de Comandos/Funções:** O servidor expõe única e exclusivamente a ferramenta `@mcp.tool() salvar_plano_estudos`. Nenhuma outra função do sistema ou do interpretador Python está disponível para o agente LLM.
* **Limitar Acesso a Arquivos/Pastas:** A ferramenta MCP possui um diretório de trabalho isolado em código (`workspace_dir = "planos_gerados"`). Adicionalmente, o nome do arquivo sofre sanitização estrita para evitar vulnerabilidades de *Path Traversal*, garantindo que o agente jamais consiga ler ou escrever fora dessa pasta permitida.
* **Registrar Chamadas de Tool:** Todas as execuções da ferramenta geram registros locais obrigatórios. O servidor utiliza a biblioteca `logging` nativa do Python para registrar parâmetros de entrada (como nome do aluno e disciplinas solicitadas) no arquivo físico `mcp_security.log`, permitindo auditoria do comportamento do modelo.
* **Justificativa de Escolha e Riscos:** Optou-se pela construção de um MCP Próprio Local ao invés de soluções de terceiros (Opção 2) visando o conceito de *Zero Trust*. Em um cenário acadêmico real, plugar um MCP externo ou dar acesso direto de gravação a um banco de dados (SIGAA) apresenta alto risco de corrupção de histórico acadêmico devido a alucinações. O uso de um MCP local como "Middleware" (que apenas recebe as intenções e aplica a regra dura via código seguro) anula o risco do LLM aprovar matrículas indevidas.

## Setup (mínimo)

1. Clonar o repositório:
   git clone <repo-url>
   cd <nome-da-pasta>

2. Criar ambiente virtual:
   python3 -m venv .venv 
   source .venv/bin/activate  # No Windows use: .venv\Scripts\activate

3. Instalar dependências:
   python3 -m pip install --no-cache --no-deps -r requirements.txt

4. Ingestão de Dados (Indexação):
   - Certifique-se de que os PDFs do curso (resoluções, regulamentos) e o arquivo `resumo_prerequisitos.txt` estão na pasta `data/pdfs/`.
   - Crie o banco vetorial rodando:
   python3 src/retriever.py

5. Gerar o `perguntas_com_gabarito.jsonl`:
   - python src/gen_gabarito.py --in eval/eval_questions.jsonl --out eval/perguntas_com_gabarito.jsonl

6. Rodar a aplicação:
   PYTHONPATH=. streamlit run app/streamlit_app.py

## Execução local com Ollama

- Instale o Ollama (https://ollama.com)
- Baixe o modelo padrão do projeto (Mistral):
  ollama pull mistral
- (Opcional) Configure a variável de ambiente:
  export OLLAMA_MODEL=mistral

## Avaliação para cada métrica

*(Esta seção será atualizada com os resultados finais das avaliações)*

1. Avaliar Fidelidade (Faithfulness - HHEM):
   PYTHONPATH=. python eval/eval_ragas.py --data eval/perguntas_com_gabarito.jsonl --mode chat --metric faithfulness_hhem --outdir reports

2. Avaliar Relevância da Resposta (Answer Relevancy):
   PYTHONPATH=. python eval/eval_ragas.py --data eval/perguntas_com_gabarito.jsonl --mode chat --metric answer_relevancy --outdir reports