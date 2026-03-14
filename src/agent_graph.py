from __future__ import annotations
from typing import TypedDict, Literal, List, Dict, Any, Optional
import os, re, unicodedata

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.retriever import PDFIndexerRetriever
from src.answer_agent import generate as generate_answer
from src.selfcheck import extract_claims, check_claims_and_rewrite

class State(TypedDict, total=False):
    question: str
    mode: Literal["chat", "detector", "automation"]
    history: List[Dict[str, str]]
    intent: Literal["qa", "detector", "automation", "blocked"]
    evidences: List[Dict[str, Any]]
    draft: str
    final: str
    sensitive_category: Optional[str]
    retries: int 

SIM_THRESHOLD = 0.50


def _normalize_mcp_result(raw: Any) -> str:
    """Converte retorno bruto da tool MCP em texto legivel para UI."""
    if raw is None:
        return "Sem retorno da ferramenta MCP."

    if isinstance(raw, str):
        return raw

    if isinstance(raw, dict):
        if isinstance(raw.get("text"), str):
            return raw["text"]
        if isinstance(raw.get("content"), str):
            return raw["content"]
        if isinstance(raw.get("content"), list):
            parts = []
            for item in raw["content"]:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
            if parts:
                return "\n".join(parts)
        return str(raw)

    if isinstance(raw, list):
        parts = []
        for item in raw:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        if parts:
            return "\n".join(parts)
        return str(raw)

    return str(raw)

def _router(state: State) -> Dict[str, Any]:
    return {"intent": state.get("mode", "chat")}

def _retrieve(state: State, retriever: PDFIndexerRetriever) -> Dict[str, Any]:
    q = state.get("question")
    hits = retriever.retrieve(q, k=3) # V3 fixo em K=3
    return {"evidences": hits}

def _answer(state: State) -> Dict[str, Any]:
    if state.get("intent") == "blocked":
        return {}
    hits = state.get("evidences", [])
    draft = generate_answer(
        user_query=state.get("question"),
        hits=hits,
        history=state.get("history", []),
        prompt_type="chat"
    )
    return {"draft": draft}

def _selfcheck(state: State, retriever: PDFIndexerRetriever) -> Dict[str, Any]:
    if state.get("intent") == "blocked":
        return {"final": state.get("draft")}

    draft = state.get("draft") or ""
    retries = state.get("retries", 0)

    if not draft.strip() or "NÃO ENCONTREI BASE" in draft:
        if retries < 1:
            print(f"[Self-Check] Falhou na tentativa {retries}. Tentando re-busca...")
            return {"retries": retries + 1, "final": "REBUSCAR"}
        else:
            return {"final": "Não encontrei evidências suficientes nos regulamentos para responder com segurança."}

    claims = extract_claims(draft)
    final = check_claims_and_rewrite(
        draft=draft,
        claims=claims,
        retriever=retriever,
        min_sim=SIM_THRESHOLD,
        min_overlap_terms=1,
    )
    return {"final": final}

def _automation_agent(state: State) -> Dict[str, Any]:
    question = state.get("question", "")
    from src.answer_agent import _ollama_client, OLLAMA_MODEL
    prompt_extracao = f"Extraia apenas os nomes das disciplinas que o aluno quer cursar da frase a seguir. Retorne apenas os nomes separados por vírgula, sem texto extra. Frase: '{question}'"
    
    try:
        cliente = _ollama_client()
        resposta = cliente.generate(model=OLLAMA_MODEL, prompt=prompt_extracao)
        disciplinas_str = resposta["response"].strip()
    except Exception:
        disciplinas_str = question 

    plano_recomendado = "O agente analisou as diretrizes do curso e aplicou as regras de pré-requisitos locais."
    nome_aluno = "Aluno_Demo"
    
    import asyncio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from langchain_mcp_adapters.tools import load_mcp_tools

    async def run_mcp_adapter():
        server_params = StdioServerParameters(
            command="python",
            args=[os.path.abspath("mcp_server.py")], 
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await load_mcp_tools(session)
                mcp_tool = next((t for t in tools if t.name == "salvar_plano_estudos"), None)
                if mcp_tool:
                    return await mcp_tool.ainvoke({
                        "nome_aluno": nome_aluno,
                        "plano_recomendado": plano_recomendado,
                        "disciplinas_pretendidas": disciplinas_str
                    })
                return "Ferramenta salvar_plano_estudos não encontrada no Servidor MCP."

    try:
        mcp_resultado = asyncio.run(run_mcp_adapter())
        mcp_resultado_txt = _normalize_mcp_result(mcp_resultado)
        final_answer = (
            "**Automação via Adapter MCP (stdio) executada com sucesso!**\n\n"
            f"Disciplinas lidas: `{disciplinas_str}`\n\n{mcp_resultado_txt}"
        )
    except Exception as e:
         final_answer = f"⚠️ Erro de conexão com o Servidor MCP: {e}"

    return {"final": final_answer}

def build_app(retriever: PDFIndexerRetriever):
    g = StateGraph(State)
    g.add_node("router", _router)
    g.add_node("retrieve", lambda s: _retrieve(s, retriever))
    g.add_node("answer", _answer)
    g.add_node("selfcheck", lambda s: _selfcheck(s, retriever))
    g.add_node("automation", _automation_agent)

    g.set_entry_point("router")
    
    g.add_conditional_edges(
        "router",
        lambda s: "automation" if s.get("intent") == "automation" else "retrieve",
    )
    
    g.add_edge("retrieve", "answer")
    g.add_edge("answer", "selfcheck")
    g.add_edge("selfcheck", END)
    g.add_edge("automation", END)

    return g.compile(checkpointer=MemorySaver())