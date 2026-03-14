import os
import re
import ollama

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

def _ollama_client():
    return ollama.Client(host=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))

def generate(user_query: str, hits: list, history: list = None, prompt_type: str = "chat"):
    client = _ollama_client()
    
    context_text = ""
    for i, hit in enumerate(hits, 1):
        content = hit.get("text", "").strip()
        source = hit.get("meta", {}).get("source", "Documento desconhecido")
        context_text += f"--- TRECHO {i} (Fonte: {source}) ---\n{content}\n\n"

    system_instruction = (
        "Você é um Assistente Acadêmico da UFCG estritamente fiel aos documentos fornecidos.\n"
        "REGRAS CRÍTICAS DE RESPOSTA:\n"
        "1. Use APENAS as informações contidas nos trechos de contexto abaixo.\n"
        "2. Se a informação não estiver presente no contexto, responda exatamente: 'NÃO ENCONTREI BASE NOS DOCUMENTOS'.\n"
        "3. PROIBIDO usar conhecimento prévio sobre outras universidades ou senso comum.\n"
        "4. Seja amigável, direto e técnico.\n"
        "5. É ESTRITAMENTE PROIBIDO citar fontes, 'Trechos', páginas ou nomes de arquivos na sua resposta. Apenas entregue a informação pura."
    )

    full_prompt = f"""{system_instruction}

CONTEXTO DISPONÍVEL:
{context_text}

PERGUNTA DO ALUNO:
{user_query}

RESPOSTA FIEL:"""

    response = client.generate(
        model=OLLAMA_MODEL,
        prompt=full_prompt,
        options={
            "temperature": 0.0,       
            "num_predict": 700,       
            "top_p": 0.1,             
            "stop": ["---", "DÚVIDA"]
        }
    )

    
    draft = response["response"]
    draft = re.sub(r'\(?Fonte:.*?\)?', '', draft, flags=re.IGNORECASE)
    draft = re.sub(r'(Segundo|Conforme) o (TRECHO|documento).*?,?', '', draft, flags=re.IGNORECASE)
    draft = re.sub(r'\[.*?\]', '', draft)
    
    return draft.strip()