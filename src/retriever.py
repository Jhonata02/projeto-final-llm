from __future__ import annotations
import argparse
import hashlib
import os
import re
import unicodedata
from typing import List
import chromadb
from chromadb.utils import embedding_functions
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from docling.document_converter import DocumentConverter
    from docling_core.types.doc import ImageRefMode
except ImportError:  # pragma: no cover - depende do ambiente local
    DocumentConverter = None
    ImageRefMode = None

def clean_text(text: str) -> str:
    """Limpa ruídos comuns de extração de PDF para melhorar a busca vetorial."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r'(?<=[^\.!\?])\n+(?=[a-z])', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'Página \d+ de \d+', '', text, flags=re.IGNORECASE)
    return text.strip()

class PDFIndexerRetriever:
    def __init__(self, collection_name: str = "pdfs_rag"):
        self.client = chromadb.PersistentClient(path="data/chroma_store")
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=ef,
        )
        self.converter = DocumentConverter() if DocumentConverter is not None else None
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200,
            separators=["\nArt.", "\n§", "\nArt", ". ", " ", ""]
        )

    def ensure_ready(self) -> None:
        """Garante que a collection já possua dados indexados."""
        if self.collection.count() == 0:
            raise RuntimeError(
                "Collection vazia. Rode a ingestao/indexacao antes de consultar."
            )

    def load_pdfs(self, pdf_paths):
        if pdf_paths and self.converter is None:
            return []
        all_docs = []
        for path in pdf_paths:
            dldoc = self.converter.convert(path).document
            basename = os.path.basename(path)
            n_pages = dldoc.num_pages()
            for p in range(1, n_pages + 1):
                md_text = dldoc.export_to_markdown(
                    page_no=p,  
                    image_mode=ImageRefMode.PLACEHOLDER,
                    image_placeholder=''
                )
                cleaned_text = clean_text(md_text)
                if cleaned_text:
                    all_docs.append(Document(page_content=cleaned_text, metadata={"source": basename, "page": p}))
        return all_docs

    def load_txts(self, txt_paths: List[str]) -> List[Document]:
        all_docs: List[Document] = []
        for path in txt_paths:
            with open(path, "r", encoding="utf-8") as f:
                content = clean_text(f.read())
            if content:
                all_docs.append(
                    Document(
                        page_content=content,
                        metadata={"source": os.path.basename(path), "page": None},
                    )
                )
        return all_docs

    def _stable_id(self, text: str, meta: dict) -> str:
        base = f"{meta.get('source','pdf')}|{meta.get('page','')}"
        h = hashlib.sha1((base + "|" + text.strip()).encode("utf-8")).hexdigest()
        return f"doc_{h}"

    def chunk_and_index(self, docs):
        chunks = self.splitter.split_documents(docs)
        texts = [d.page_content for d in chunks]
        metadatas = []
        for idx, d in enumerate(chunks):
            m = dict(d.metadata or {})
            m.setdefault("source", "pdf")
            m.setdefault("page", None)
            m["chunk"] = idx
            metadatas.append(m)
        ids = [self._stable_id(t, m) for t, m in zip(texts, metadatas)]
        self.collection.upsert(documents=texts, metadatas=metadatas, ids=ids)

    def build_index_from_folder(self, folder_path: str) -> None:
        files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)]
        pdfs = [f for f in files if f.lower().endswith(".pdf")]
        txts = [f for f in files if f.lower().endswith(".txt")]
        if pdfs and self.converter is None and not txts:
            raise RuntimeError(
                "Foram encontrados PDFs, mas o parser de PDF (docling) nao esta disponivel. "
                "Instale as dependencias ou inclua .txt na pasta para indexacao."
            )
        if pdfs and self.converter is None and txts:
            print(
                "[Aviso] PDFs ignorados porque docling nao esta disponivel. "
                "Indexando apenas arquivos .txt."
            )
        docs = self.load_pdfs(pdfs) + self.load_txts(txts)
        if not docs:
            raise ValueError(f"Nenhum documento .pdf/.txt encontrado em {folder_path}.")
        self.client.delete_collection(name=self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name, embedding_function=self.collection._embedding_function
        )
        self.chunk_and_index(docs)

    def retrieve(self, query: str, k: int = 5):
        res = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"],  
        )
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        ids   = res.get("ids", [[]])[0]   

        hits = []
        for _id, doc, meta, dist in zip(ids, docs, metas, dists):
            sim = 1.0 - float(dist)  
            hits.append({"id": _id, "text": doc, "metadata": meta, "distance": dist, "similarity": sim})
        hits.sort(key=lambda h: h["similarity"], reverse=True)
        return hits


def main() -> None:
    parser = argparse.ArgumentParser(description="Indexa corpus local no ChromaDB.")
    parser.add_argument(
        "--folder",
        default="data/pdfs",
        help="Pasta com documentos .pdf/.txt para indexacao.",
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
        f"Indexacao concluida. Collection '{args.collection}' com "
        f"{retriever.collection.count()} chunks."
    )


if __name__ == "__main__":
    main()