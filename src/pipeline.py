from __future__ import annotations
from typing import Literal, Optional, List, Dict

from src.retriever import PDFIndexerRetriever
from src.agent_graph import build_app  

_retriever: Optional[PDFIndexerRetriever] = None
_app = None
DEFAULT_CORPUS_FOLDER = "data/pdfs"

def get_retriever() -> PDFIndexerRetriever:
    global _retriever
    if _retriever is None:
        _retriever = PDFIndexerRetriever()
        try:
            _retriever.ensure_ready()
        except RuntimeError as exc:
            try:
                _retriever.build_index_from_folder(DEFAULT_CORPUS_FOLDER)
            except ValueError as build_exc:
                raise RuntimeError(
                    "Retriever sem indice e sem documentos para indexacao em "
                    f"'{DEFAULT_CORPUS_FOLDER}'."
                ) from build_exc
            _retriever.ensure_ready()
    return _retriever

def get_app():
    global _app
    if _app is None:
        retr = get_retriever()
        _app = build_app(retriever=retr)
    return _app

def run_pipeline(
    mode: Literal["chat", "detector", "automation"], # <-- Adicionado automation
    user_input: str,
    history: Optional[List[Dict[str, str]]] = None
) -> str:
    app = get_app()
    state = {
        "question": user_input,
        "mode": mode,
        "history": history or [],
    }
    out = app.invoke(state, config={"configurable": {"thread_id": "main"}})
    final = out.get("final") or out.get("draft") or "NÃO ENCONTREI BASE"
    #final = add_disclaimer(final, mode)
    return final