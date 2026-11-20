# Imagen unica para la API y para el frontend: el mismo codigo, distinto comando.
# El comando por defecto arranca la API; docker-compose lo sobreescribe para Streamlit.
FROM python:3.12-slim

# uv con version fijada, copiado desde su imagen oficial
COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

# Dependencias primero: esta capa solo se reconstruye si cambian pyproject.toml o uv.lock
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

# Despues el codigo, que es lo que cambia en cada commit
COPY app ./app
COPY frontend ./frontend
COPY models ./models

RUN uv sync --frozen

# Usuario sin privilegios
RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
