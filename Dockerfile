# ==============================================================================
# ETAPA 1: BUILDER (Construcción y Compilación)
# Esta etapa instala las herramientas pesadas de compilación del sistema y 
# descarga todas las dependencias de Python descritas en requirements.txt.
# ==============================================================================
FROM python:3.11-slim AS builder

# Desactiva la generación de archivos .pyc (bytecode) para ahorrar espacio en disco
ENV PYTHONDONTWRITEBYTECODE=1

# Fuerza a Python a enviar logs (print) directamente a la consola sin almacenamiento en buffer
ENV PYTHONUNBUFFERED=1

# Establece el directorio de trabajo dentro del contenedor donde se ejecutarán las instrucciones
WORKDIR /app

# Actualiza el gestor de paquetes de Linux (apt) e instala compiladores C (build-essential) 
# y cabeceras de desarrollo de PostgreSQL (libpq-dev) necesarios para compilar librerías como psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia únicamente el archivo de dependencias desde la máquina local al contenedor
COPY requirements.txt .

# Instala los paquetes de Python dentro de un directorio aislado (/install) para copiarlos fácilmente después
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


# ==============================================================================
# ETAPA 2: RUNNER (Contenedor Final de Ejecución)
# Esta etapa toma las librerías ya procesadas de la etapa previa y el código fuente.
# Genera una imagen limpia y liviana, sin herramientas innecesarias de compilación.
# ==============================================================================
FROM python:3.11-slim AS runner

# Mantiene las optimizaciones de variables de entorno de Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Reestablece el directorio de trabajo del entorno final
WORKDIR /app

# Instala únicamente librerías de tiempo de ejecución (libpq5 para Postgres y curl para pruebas de red)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia las librerías de Python instaladas desde la etapa 'builder' al directorio del sistema
COPY --from=builder /install /usr/local

# Copia el código fuente de la aplicación desde la carpeta local ./app hacia /app/app en el contenedor
COPY ./app /app/app

# Declara de forma documental que la aplicación escucha en el puerto 8000
EXPOSE 8000

# Comando ejecutable por defecto para arrancar el servidor ASGI Uvicorn apuntando al entrypoint de FastAPI
CMD ["uvicorn", "app.entrypoints.api.v1.main:app", "--host", "0.0.0.0", "--port", "8000"]