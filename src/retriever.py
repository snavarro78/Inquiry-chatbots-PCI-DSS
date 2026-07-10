from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_DIR = str(PROJECT_ROOT / "db")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def cargar_db() -> Chroma:
    """Carga la base vectorial existente desde disco."""
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    db = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embeddings,
        collection_name="pci_dss"
    )
    return db


def buscar_contexto(pregunta: str, db: Chroma, n_resultados: int = 4) -> tuple:
    """
    Busca los chunks más relevantes para la pregunta.
    Convierte la pregunta en vector y calcula similitud coseno
    contra todos los chunks guardados en ChromaDB.
    """
    resultados = db.similarity_search(pregunta, k=n_resultados)

    contexto = ""
    for i, doc in enumerate(resultados):
        fuente = doc.metadata.get("source_file", "PCI DSS")
        pagina = doc.metadata.get("page", "?")
        contexto += f"[Fragmento {i+1} — {fuente}, p.{pagina}]\n"
        contexto += doc.page_content + "\n\n"

    return resultados, contexto