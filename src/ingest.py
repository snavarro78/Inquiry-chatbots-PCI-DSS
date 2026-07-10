import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
load_dotenv()

# Rutas
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PDF_PATH = PROJECT_ROOT / "data" / "PCI-DSS-v4_0_1-LA.pdf"
DB_DIR = str(PROJECT_ROOT / "db")

# Modelo de embeddings (corre local, sin costo)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def cargar_pdf() -> list:
    """Carga el PDF y devuelve sus páginas."""
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"No se encontró el PDF en: {PDF_PATH}")

    print(f"Leyendo documento: {PDF_PATH.name}")
    loader = PyPDFLoader(str(PDF_PATH))
    paginas = loader.load()

    # Agregar metadato con nombre del archivo
    for pagina in paginas:
        pagina.metadata["source_file"] = PDF_PATH.name

    print(f"Páginas extraídas: {len(paginas)}")
    return paginas


def dividir_en_chunks(paginas: list) -> list:
    """
    Divide las páginas en fragmentos más pequeños.

    chunk_size=800: tamaño máximo de cada fragmento en caracteres
    chunk_overlap=100: caracteres que se repiten entre chunks contiguos
                       para no perder contexto en los bordes
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_documents(paginas)
    print(f"Chunks generados: {len(chunks)}")
    return chunks


def crear_base_vectorial(chunks: list) -> Chroma:
    """
    Genera embeddings para cada chunk y los guarda en ChromaDB.

    Los embeddings son vectores numéricos que representan el significado
    del texto. ChromaDB los almacena en disco en la carpeta db/ para
    no tener que recalcularlos cada vez que el usuario haga una pregunta.
    """
    print("Generando embeddings (puede tardar unos minutos)...")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"}
    )

    # Chroma.from_documents() hace dos cosas:
    # 1. Convierte cada chunk en un vector usando el modelo de embeddings
    # 2. Guarda todos los vectores en disco en DB_DIR
    db = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=DB_DIR,
        collection_name="pci_dss"
    )

    print(f"Base vectorial guardada en: {DB_DIR}")
    return db


def main() -> None:
    print("=== Iniciando ingestión de documentos PCI DSS ===\n")

    print("1. Cargando PDF...")
    paginas = cargar_pdf()

    print("\n2. Dividiendo en chunks...")
    chunks = dividir_en_chunks(paginas)

    print("\n3. Creando base vectorial en ChromaDB...")
    db = crear_base_vectorial(chunks)

    print("\n=== Ingestión completada ===")
    print(f"  Páginas procesadas: {len(paginas)}")
    print(f"  Chunks almacenados: {len(chunks)}")


if __name__ == "__main__":
    main()