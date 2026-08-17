import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from retriever import cargar_db, buscar_contexto

load_dotenv()

SYSTEM_PROMPT = """Eres un experto consultor en seguridad de pagos especializado en PCI DSS v4.0.1.
Respondes preguntas de equipos de seguridad, auditoría y cumplimiento de manera clara y profesional.

Instrucciones:
- Responde de forma directa y natural, como lo haría un experto humano explicando el tema.
- NO uses frases como "según el fragmento", "en el contexto proporcionado" o "los fragmentos indican". 
  En su lugar usa "según PCI DSS", "el estándar establece", "PCI DSS v4.0.1 requiere", etc.
- Cita los números de requisito y sub-requisito cuando estén disponibles (ej: Requisito 10.3.1).
- Usa listas con viñetas o numeradas cuando haya varios puntos, para facilitar la lectura.
- Si hay buenas prácticas adicionales mencionadas, inclúyelas al final.
- Responde siempre en español.
- No escribas las páginas utilizadas dentro de la respuesta; el sistema las agregará automáticamente.

REGLA CRÍTICA SOBRE ALUCINACIONES:
- NUNCA inventes datos específicos como nombres de algoritmos, versiones, tamaños de clave,
  números de requisito o fechas si no están literalmente en el contexto proporcionado.
- Si el contexto no tiene información suficiente, di exactamente:
  "El estándar PCI DSS aborda este tema en el Requisito [X], pero la sección específica 
  no está disponible en el contexto actual. Te recomiendo consultar directamente esa 
  sección del documento oficial."
- Es mejor admitir que no tienes el dato exacto que inventarlo.
"""

# Temas fuera del alcance del asistente
TEMAS_FUERA_DE_ALCANCE = [
    "iso 27001", "iso27001", "soc 2", "soc2", "nist", "hipaa", "gdpr",
    "costo", "precio", "cuanto cuesta", "cuánto cuesta", "cuánto vale",
    "cuanto vale", "tarifa", "presupuesto", "pagar", "factura",
    "clima", "deporte", "política", "receta", "película", "canción"
]


def es_fuera_de_alcance(pregunta: str) -> bool:
    """Verifica si la pregunta está fuera del alcance del asistente PCI DSS."""
    pregunta_lower = pregunta.lower()
    return any(tema in pregunta_lower for tema in TEMAS_FUERA_DE_ALCANCE)


class PCIChatbot:
    def __init__(self):
        self.db = cargar_db()
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0.1
        )
        self.historial = []

    def responder(self, pregunta: str) -> dict:
        # Verificar si la pregunta está fuera del alcance
        if es_fuera_de_alcance(pregunta):
            return {
                "respuesta": "Esta consulta está fuera del alcance de este asistente, "
                             "que está especializado en PCI DSS v4.0.1. ¿Tienes alguna "
                             "pregunta sobre los requisitos, controles o el proceso de "
                             "certificación PCI DSS?",
                "fuentes": []
            }

        # Paso 1: recuperar contexto relevante
        documentos, contexto = buscar_contexto(pregunta, self.db)

        # Paso 2: construir el prompt con el contexto recuperado
        prompt_usuario = f"""Contexto de documentos oficiales PCI DSS:
{contexto}

Pregunta: {pregunta}
"""

        # Paso 3: llamar al LLM con historial
        mensajes = [
            SystemMessage(content=SYSTEM_PROMPT),
            *self.historial,
            HumanMessage(content=prompt_usuario)
        ]

        respuesta = self.llm.invoke(mensajes)

        # Mantener últimas 6 interacciones en historial
        self.historial.append(HumanMessage(content=pregunta))
        self.historial.append(respuesta)
        if len(self.historial) > 12:
            self.historial = self.historial[-12:]

        # Paso 4: armar fuentes
        fuentes = []
        for doc in documentos:
            fuentes.append({
                "archivo": doc.metadata.get("source_file", "PCI DSS"),
                "pagina": doc.metadata.get("page", "?"),
                "fragmento": doc.page_content[:150] + "..."
            })

        # Obtener páginas únicas utilizadas
        paginas = sorted({
            fuente["pagina"]
            for fuente in fuentes
            if fuente["pagina"] != "?"
        })

        if paginas:
            texto_paginas = ", ".join(str(pagina) for pagina in paginas)
            respuesta_final = (
                f"{respuesta.content}\n\n"
                f"Páginas consultadas: {texto_paginas}."
            )
        else:
            respuesta_final = respuesta.content

        return {
            "respuesta": respuesta_final,
            "fuentes": fuentes
        }