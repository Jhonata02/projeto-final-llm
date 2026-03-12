# src/safety.py
from __future__ import annotations

def add_disclaimer(text: str, mode: str = "chat") -> str:
    base = "\n\n> **Aviso de Segurança**: Conteúdo gerado automaticamente com base em documentos públicos. Consulte sempre a coordenação do curso ou o sistema acadêmico oficial antes de tomar decisões definitivas sobre sua matrícula."
    return text + base