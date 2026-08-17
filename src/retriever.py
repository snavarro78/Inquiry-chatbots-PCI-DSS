import re
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


def enriquecer_pregunta(pregunta: str) -> str:
    import re
    pregunta_lower = pregunta.lower()

    # Mapa de requisitos a sus términos técnicos
    terminos_por_requisito = {
        "1":  "firewall red configuración seguridad perímetro",
        "2":  "configuración predeterminada contraseñas parámetros sistemas",
        "3":  "datos tarjetahabiente almacenamiento PAN protección cifrado",
        "4":  "cifrado transmisión tránsito criptografía TLS datos",
        "5":  "malware antivirus software malicioso protección",
        "6":  "sistemas seguros desarrollo vulnerabilidades parches aplicaciones",
        "7":  "acceso datos necesidad conocer restricción autorización",
        "8":  "autenticación identidad usuarios contraseñas MFA acceso",
        "9": "acceso físico dispositivos punto venta POI terminales visitantes badges entrada restringir cámaras",
        "10": "registros auditoría logs monitoreo acceso eventos supervisión",
        "11": "pruebas seguridad vulnerabilidades penetración escaneo ASV",
        "12": "políticas procedimientos seguridad información programa",
    }

    # Enriquecer por número de requisito
    match = re.search(r'requisito\s+(\d+)', pregunta_lower)
    if match:
        numero = match.group(1)
        terminos = terminos_por_requisito.get(numero, "controles seguridad cumplimiento")
        return f"{pregunta} {terminos}"

    # Enriquecer por tema técnico aunque no mencione número de requisito
    temas = {
        "cifrado": "criptografía sólida algoritmos AES TLS requisito 3 4 cifrado datos",
        "protocolo": "TLS SSL criptografía transmisión requisito 4 cifrado protocolo",
        "tls": "TLS SSL protocolo cifrado transmisión requisito 4 criptografía",
        "ssl": "SSL TLS protocolo obsoleto requisito 4 Anexo A2",
        "cde": "CDE cardholder data environment entorno datos tarjetahabiente",
        "reposo": "cifrado almacenamiento PAN datos reposo requisito 3 ilegible",
        "tránsito": "cifrado transmisión TLS datos tránsito requisito 4",
        "autenticación": "MFA multifactor autenticación requisito 8 acceso identidad",
        "contraseña": "contraseñas autenticación requisito 8 usuarios acceso",
        "firewall": "firewall red configuración requisito 1 perímetro seguridad",
        "vulnerabilidad": "vulnerabilidades escaneo parches requisito 6 11 ASV",
        "auditoría": "registros auditoría logs monitoreo requisito 10 eventos",
        "escaneo": "escaneo ASV vulnerabilidades externo requisito 11",
        "asv": "ASV proveedor escaneo aprobado vulnerabilidades requisito 11",
        "penetración": "pruebas penetración pen test requisito 11 seguridad",
        "política": "políticas procedimientos seguridad requisito 12 programa",
        "física": "acceso físico hardware dispositivos requisito 9 instalaciones",
        "malware": "malware antivirus software malicioso requisito 5 protección",
        "parche": "parches actualizaciones vulnerabilidades requisito 6 sistemas",
        "criptografía": "criptografía sólida AES RSA algoritmos cifrado requisito 3 4",
        "algoritmo": "algoritmos cifrado AES RSA criptografía sólida requisito 3 4",
    }

    for palabra_clave, enriquecimiento in temas.items():
        if palabra_clave in pregunta_lower:
            return f"{pregunta} {enriquecimiento}"

    return pregunta


def buscar_contexto(pregunta: str, db: Chroma, n_resultados: int = 6) -> tuple:
    """
    Busca los chunks más relevantes para la pregunta.
    Usa n_resultados=6 para tener más contexto disponible.
    """
    # Enriquecer la pregunta para mejorar la búsqueda
    pregunta_enriquecida = enriquecer_pregunta(pregunta)

    resultados = db.similarity_search(pregunta_enriquecida, k=n_resultados)

    contexto = ""
    for i, doc in enumerate(resultados):
        fuente = doc.metadata.get("source_file", "PCI DSS")
        pagina = doc.metadata.get("page", "?")
        contexto += f"[Sección del estándar — {fuente}, p.{pagina}]\n"
        contexto += doc.page_content + "\n\n"

    return resultados, contexto