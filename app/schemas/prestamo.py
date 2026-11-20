from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PrestamoEntrada(BaseModel):
    """Datos de una solicitud de prestamo. Contrato de entrada del modelo."""

    model_config = ConfigDict(extra="forbid")

    edad: int = Field(ge=18, le=75, description="Edad del solicitante en años cumplidos")
    ingresos_mensuales: float = Field(gt=0, description="Ingresos netos mensuales en euros")    
    importe_prestamo: float = Field(gt=0, description="Importe solicitado en euros")
    plazo_meses: int = Field(ge=6, le=84, description="Plazo de devolucion en meses (no años)")
    antiguedad_laboral_anios: int = Field(ge=0, le=50, description="Años trabajados en el empleo actual")
    impagos_previos: int = Field(ge=0, le=20, description="Numero de impagos registrados en el historial")

    @field_validator("antiguedad_laboral_anios")
    @classmethod
    def validar_antiguedad(cls, valor, info):
        edad = info.data.get("edad")
        if edad is not None and valor > edad - 16:
            raise ValueError("antiguedad_laboral_anios no puede ser mayor que edad - 16")
        return valor


class PrediccionSalida(BaseModel):
    """Resultados de la prediccion. Contrato de salida del modelo"""

    probabilidad_impago: float = Field(ge=0, le=1, description="Probabilidad estimada de impago, entre 0 y 1")
    decision: Literal["aprobar", "revisar", "rechazar"] = Field(description="Decision derivada de la probabilidad segun los umbrales")
