from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader


# Ruta principal del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Ruta del PDF
PDF_PATH = PROJECT_ROOT / "data" / "PCI-DSS-v4_0_1-LA.pdf"


def cargar_pdf() -> list:
    """Carga el PDF y devuelve sus páginas."""

    if not PDF_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo PDF en: {PDF_PATH}"
        )

    print(f"Leyendo documento: {PDF_PATH.name}")

    loader = PyPDFLoader(str(PDF_PATH))
    paginas = loader.load()

    print(f"Páginas extraídas correctamente: {len(paginas)}")

    return paginas


def main() -> None:
    paginas = cargar_pdf()

    print("\n--- Muestra del texto extraído ---")
    print(paginas[0].page_content[:500])


if __name__ == "__main__":
    main()