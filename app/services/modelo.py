import joblib

from app.config import MODEL_PATH
from app.schemas.prestamo import PrediccionSalida

# Orden en el que el modelo espera las variables
VARIABLES = [
    "edad",
    "ingresos_mensuales",
    "importe_prestamo",
    "plazo_meses",
    "antiguedad_laboral_anios",
    "impagos_previos",
]


MODELO = joblib.load(MODEL_PATH)

def decidir(probabilidad):
    """Traduce una probabilidad de impago en una decision"""
    if probabilidad < 0.2:
        return "aprobar"
    elif probabilidad < 0.5:
        return "revisar"
    return "rechazar"

def predecir(entrada):
    """Aplica el modelo a una solicitud validada y devuelve la salida del contrato"""
    datos = entrada.model_dump()
    fila = [datos[variable] for variable in VARIABLES]
    probabilidad = float(MODELO.predict_proba([fila])[0][1])
    return PrediccionSalida(
        probabilidad_impago=probabilidad, decision=decidir(probabilidad)
    )
