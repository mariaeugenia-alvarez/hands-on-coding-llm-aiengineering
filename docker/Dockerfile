FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (cache de Docker layers)
COPY requirements.txt .

# Instalar torch CPU-only (reduce imagen de ~2GB a ~200MB)
RUN pip install --no-cache-dir torch==2.2.2 --index-url https://download.pytorch.org/whl/cpu

# Instalar resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo fuente (incluye DB con datos y vectorstore FAISS)
COPY . .

EXPOSE 5001

CMD ["python", "app.py"]
