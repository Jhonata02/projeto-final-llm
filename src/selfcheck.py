from __future__ import annotations
from typing import List, Dict, Any
import re
import os

from src.retriever import PDFIndexerRetriever

def _sentences(text: str) -> List[str]:
    # Melhora a quebra de sentenças para evitar fragmentos órfãos
    parts = re.split(r'(?<=[\.\!\?])\s+', (text or "").strip())
    return [p.strip() for p in parts if len(p.strip()) > 10]

def _overlap(a: str, b: str) -> int:
    toks_a = set(w.lower() for w in re.findall(r"\w+", a or ""))
    toks_b = set(w.lower() for w in re.findall(r"\w+", b or ""))
    return len(toks_a & toks_b)

def _sim_of(hit: Dict[str, Any]) -> float:
    if not hit: return 0.0
    sim = hit.get("similarity")
    if sim is not None:
        return float(sim)
    dist = hit.get("distance")
    # Inversão correta para garantir que scores altos signifiquem proximidade
    return (1.0 - float(dist)) if dist is not None else 0.0

def extract_claims(text: str) -> List[str]:
    sents = _sentences(text)
    # Ignora frases muito curtas que o LLM usa como transição, focando em fatos
    return [s for s in sents if len(re.findall(r"\w+", s)) >= 6][:15]

def _find_supports_for_claim(
    claim: str,
    retriever: PDFIndexerRetriever,
    min_sim: float = 0.45,
    min_overlap_terms: int = 1,
    k: int = 8,
) -> List[Dict[str, Any]]:
    hits = retriever.retrieve(claim, k=k)
    if not hits:
        return []
    
    accepted = [
        h for h in hits 
        if _sim_of(h) >= min_sim and _overlap(claim, h.get("text", "")) >= min_overlap_terms
    ]
    accepted.sort(key=_sim_of, reverse=True)
    return accepted[:1] 

def check_claims_and_rewrite(
    draft: str,
    claims: List[str],
    retriever: PDFIndexerRetriever,
    min_sim: float = 0.45,
    min_overlap_terms: int = 1,
) -> str:
    kept_lines: List[str] = []
    
    for sent in _sentences(draft):
        supports = _find_supports_for_claim(
            claim=sent,
            retriever=retriever,
            min_sim=min_sim,
            min_overlap_terms=min_overlap_terms,
            k=5,
        )
        
        if not supports:
            continue  

        ev = supports[0]
        meta = ev.get("meta", {}) 
        title = meta.get("source") or "Documento"
        page = meta.get("page")

        cite = f" [{os.path.basename(title)}{', p. ' + str(page) if page else ''}]"

        line = sent if cite in sent else (sent + cite)
        kept_lines.append(line)

    final = " ".join(kept_lines).strip()
    return final if len(kept_lines) >= 1 else "NÃO ENCONTREI BASE DOCUMENTAL SEGURA"