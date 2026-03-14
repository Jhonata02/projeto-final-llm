#!/usr/bin/env python3
from __future__ import annotations

import argparse

from src.retriever import PDFIndexerRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexa documentos locais para o RAG.")
    parser.add_argument(
        "--folder",
        default="data/pdfs",
        help="Pasta contendo documentos .pdf/.txt.",
    )
    parser.add_argument(
        "--collection",
        default="pdfs_rag",
        help="Nome da collection no ChromaDB.",
    )
    args = parser.parse_args()

    retriever = PDFIndexerRetriever(collection_name=args.collection)
    retriever.build_index_from_folder(args.folder)
    print(
        f"[OK] Indice reconstruido em '{args.folder}'. "
        f"Chunks totais: {retriever.collection.count()}."
    )


if __name__ == "__main__":
    main()
