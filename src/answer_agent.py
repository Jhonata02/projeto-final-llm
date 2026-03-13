import os
import ollama

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

def _ollama_client():
    return ollama.Client(host=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))

def generate(user_query: str, hits: list, history: list = None, prompt_type: str = "chat"):
    client = _ollama_client()
    
    # 1. Construção do Contexto
    context_text = ""
    for i, hit in enumerate(hits, 1):
        content = hit.get("text", "").strip()
        source = hit.get("metadata", {}).get("source", "Documento desconhecido")
        context_text += f"--- TRECHO {i} (Fonte: {source}) ---\n{content}\n\n"

    # 2. SYSTEM PROMPT BLINDADO (A chave para a Faithfulness)
    system_instruction = (
        "Você é um Assistente Acadêmico da UFCG estritamente fiel aos documentos fornecidos.\n"
        "REGRAS CRÍTICAS DE RESPOSTA:\n"
        "1. Use APENAS as informações contidas nos trechos de contexto abaixo.\n"
        "2. Se a informação não estiver presente no contexto, responda exatamente: 'NÃO ENCONTREI BASE NOS DOCUMENTOS'.\n"
        "3. PROIBIDO usar conhecimento prévio sobre outras universidades ou senso comum.\n"
        "4. Seja direto, técnico e cite o nome do arquivo da fonte (ex: [res_082017.pdf]) ao final da frase.\n"
        "5. Não tente ser útil inventando prazos ou regras que não estão no texto."
    )

    full_prompt = f"""{system_instruction}

CONTEXTO DISPONÍVEL:
{context_text}

PERGUNTA DO ALUNO:
{user_query}

RESPOSTA FIEL:"""

    # 3. PARÂMETROS DE PRECISÃO (Temperatura 0 é obrigatória)
    response = client.generate(
        model=OLLAMA_MODEL,
        prompt=full_prompt,
        options={
            "temperature": 0.0,       # Elimina a aleatoriedade
            "num_predict": 700,       # Limita o tamanho para evitar 'encheção de linguiça'
            "top_p": 0.1,             # Foca apenas nas palavras mais prováveis do contexto
            "stop": ["---", "DÚVIDA"] # Para a geração se começar a alucinar formatos
        }
    )

    return response["response"]