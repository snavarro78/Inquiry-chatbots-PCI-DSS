import re
from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


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


def extraer_palabras_clave(pregunta: str) -> list[str]:
    """Extrae términos importantes de la pregunta."""
    palabras_ignoradas = {
        "que", "qué", "como", "cómo", "cual", "cuál",
        "dice", "establece", "exige", "sobre", "según",
        "para", "del", "los", "las", "una", "uno",
        "unos", "unas", "pci", "dss"
    }

    palabras = re.findall(r"\b[\wáéíóúñ]+\b", pregunta.lower())

    return [
        palabra
        for palabra in palabras
        if len(palabra) > 2 and palabra not in palabras_ignoradas
    ]


def calcular_puntaje(texto: str, palabras_clave: list[str]) -> int:
    """Da mayor puntaje a los textos con términos de la consulta."""
    texto = texto.lower()
    puntaje = 0

    for palabra in palabras_clave:
        if palabra in texto:
            puntaje += 2

    return puntaje


def buscar_contexto(
    pregunta: str,
    db: Chroma,
    n_resultados: int = 4
) -> tuple:
    """
    Recupera varios fragmentos por similitud semántica y luego
    los reordena según coincidencias con la pregunta.
    """

    candidatos = db.similarity_search(
        pregunta,
        k=max(n_resultados * 3, 10)
    )

    palabras_clave = extraer_palabras_clave(pregunta)

    candidatos_ordenados = sorted(
        candidatos,
        key=lambda doc: calcular_puntaje(
            doc.page_content,
            palabras_clave
        ),
        reverse=True
    )

    resultados = candidatos_ordenados[:n_resultados]

    contexto = ""

    for i, doc in enumerate(resultados):
        fuente = doc.metadata.get("source_file", "PCI DSS")
        pagina = doc.metadata.get("page", "?")

        contexto += (
            f"[Fragmento {i + 1} — {fuente}, p.{pagina}]\n"
            f"{doc.page_content}\n\n"
        )

    return resultados, contexto