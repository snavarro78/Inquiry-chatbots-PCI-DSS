import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from retriever import cargar_db, buscar_contexto

load_dotenv()

SYSTEM_PROMPT = """Eres un asistente especializado en el estándar PCI DSS v4.0.1.
Tu función es responder preguntas sobre requisitos, controles y procesos de auditoría
basándote ÚNICAMENTE en el contexto de los documentos oficiales que se te proporcionan.

Reglas:
- Siempre cita el número de requisito o sección cuando sea posible.
- Si el contexto no contiene suficiente información, indícalo claramente.
- No inventes información que no esté en el contexto.
- Responde en español.
- No escribas las páginas utilizadas dentro de la respuesta; el sistema las agregará automáticamente.

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
        # Paso 1: recuperar contexto relevante
        documentos, contexto = buscar_contexto(pregunta, self.db)

        # Paso 2: construir el prompt con el contexto recuperado
        prompt_usuario = f"""Contexto de documentos oficiales PCI DSS:
{contexto}

Pregunta: {pregunta}"""

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