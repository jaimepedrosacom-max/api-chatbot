import json

from pydantic import ValidationError

from app.schemas.chat import ChatSalida, HerramientaUsada
from app.schemas.prestamo import PrestamoEntrada
from app.services.modelo import predecir

NOMBRE_TOOL = "calcular_riesgo_impago"
MAX_VUELTAS = 4

SISTEMA = (
    "Eres un asistente de riesgo de un banco. Cuando tengas todos los datos de una solicitud de "
    "prestamo, llama a la herramienta calcular_riesgo_impago. Si falta algun dato, pidelo. "
    "Nunca inventes valores. Responde en espanol y de forma breve."
)


def leer_argumentos(texto):
    """YA HECHO: convierte el texto JSON de la tool en dict ({} si no es JSON valido)."""
    try:
        datos = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return {}
    if isinstance(datos, dict):
        return datos
    return {}


def definir_tool():
    """Definicion de la tool para el LLM. El contrato sale del modelo Pydantic"""
    return {
        "type": "function",
        "function": {
            "name": NOMBRE_TOOL,
            "description": (
                "Calcula la probabilidad de impago de una solicitud de prestamo "
                "y devuelve la decision (aprobar, revisar o rechazar). "
                "Solo se puede llamar con los seis datos completos."
            ),
            "parameters": PrestamoEntrada.model_json_schema(),
        }
    }

def formatear_error(excepcion):
    """Resume un ValidationError en una linea por campo, para que el LLM se corrija."""
    partes = []
    for error in excepcion.errors():
        campo = str(error["loc"][0]) if error["loc"] else "entrada"
        partes.append(campo + ": " + error["msg"])
    return "; ".join(partes)


def ejecutar_tool(nombre, argumentos_json):
    """Valida los argumentos del LLM y llama al modelo. Nunca lanza excepciones."""
    if nombre != NOMBRE_TOOL:
        return {"ok": False, "error": "Herramienta desconocida: " + str(nombre)}

    argumentos = leer_argumentos(argumentos_json)
    if not argumentos:
        return {"ok": False, "error": "Los argumentos no son un JSON valido con datos."}

    try:
        entrada = PrestamoEntrada(**argumentos)
    except ValidationError as excepcion:
        return {"ok": False, "error": formatear_error(excepcion)}

    salida = predecir(entrada)
    return {"ok": True, **salida.model_dump()}


def responder(mensajes, llm):
    """Bucle LLM -> tool -> LLM hasta que el modelo conteste con texto."""
    historial = [{"role": "system", "content": SISTEMA}]
    for mensaje in mensajes:
        historial.append(mensaje.model_dump())

    herramientas = [definir_tool()]
    herramienta_usada = None

    for _ in range(MAX_VUELTAS):
        respuesta = llm.completar(historial, herramientas)
        llamadas = respuesta.get("tool_calls")

        if not llamadas:
            return ChatSalida(
                respuesta=respuesta.get("content") or "",
                herramienta=herramienta_usada,
            )

        llamada = llamadas[0]
        nombre = llamada["function"]["name"]
        argumentos_json = llamada["function"]["arguments"]
        resultado = ejecutar_tool(nombre, argumentos_json)

        herramienta_usada = HerramientaUsada(
            nombre=nombre,
            argumentos=leer_argumentos(argumentos_json),
            resultado=resultado,
        )

        historial.append(respuesta)
        historial.append(
            {
                "role": "tool",
                "tool_call_id": llamada["id"],
                "content": json.dumps(resultado),
            }
        )

    return ChatSalida(
        respuesta="No he podido completar la consulta. Revisa los datos e intentalo de nuevo.",
        herramienta=herramienta_usada,
    )
