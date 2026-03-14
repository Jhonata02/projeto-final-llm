from __future__ import annotations
import os, hashlib, re, unicodedata
import chromadb
from chromadb.utils import embedding_functions
from docling.document_converter import DocumentConverter
from docling_core.types.doc import ImageRefMode
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

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
        self.converter = DocumentConverter()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200,
            separators=["\nArt.", "\n§", "\nArt", ". ", " ", ""]
        )

    def ensure_ready(self):
        if self.collection.count() == 0:
            return True
        return False

    def load_pdfs(self, pdf_paths):
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
        pdfs = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
        if not pdfs: return
        self.client.delete_collection(name=self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name, embedding_function=self.collection._embedding_function
        )
        docs = self.load_pdfs(pdfs)
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
            hits.append({"id": _id, "text": doc, "meta": meta, "distance": dist, "similarity": sim})
        hits.sort(key=lambda h: h["similarity"], reverse=True)
        return hits 

if __name__ == "__main__":
    caminho_dados = "data/pdfs"
    print(f"Iniciando verificação na pasta '{caminho_dados}'...")

    if not os.path.exists(caminho_dados) or not any(f.lower().endswith('.pdf') for f in os.listdir(caminho_dados)):
        print("⚠️ ERRO: Nenhum arquivo PDF encontrado!")
        print(f"Por favor, coloque os PDFs da resolução dentro da pasta '{caminho_dados}/' e rode o script novamente.")
    else:
        print("📄 PDFs encontrados! Construindo o banco vetorial ChromaDB...")
        retriever = PDFIndexerRetriever()
        retriever.build_index_from_folder(caminho_dados)
        print("✅ Banco vetorial criado com sucesso!\n")
        
        query = "Como posso fazer minha matricula?"
        print(f"🔎 Testando busca vetorial com a query: '{query}'")
        results = retriever.retrieve(query, k=3)

        print("\n🔎 Resultados da busca:")
        for r in results:
            src  = r['meta'].get('source')
            page = r['meta'].get('page')
            sim  = r['similarity']
            snippet = r['text'][:300].replace("\n", " ") + ("..." if len(r['text']) > 300 else "")
            print(f"- Fonte: {src} (pág {page}) | Similaridade: {sim:.3f}")
            print(snippet, "\n")