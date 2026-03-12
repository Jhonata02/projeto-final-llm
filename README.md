# Assistente do Estudante - Ciência da Computação (UFCG)

PoC open-source de um sistema agêntico (RAG + LangGraph) criado para orientar alunos sobre regulamentos acadêmicos e automatizar o planejamento de matrículas respeitando árvores de pré-requisitos via Model Context Protocol (MCP local).

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