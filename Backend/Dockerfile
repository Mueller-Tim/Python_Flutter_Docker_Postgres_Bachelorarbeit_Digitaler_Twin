# ---- Basis: minimales Python 3.11-Image ----
FROM python:3.11-slim

# Benötigt für DNS-Lookups im DNS-Plugin (dig, nslookup)
RUN apt-get update && \
    apt-get install -y --no-install-recommends dnsutils && \
    rm -rf /var/lib/apt/lists/*

# Arbeits­verzeichnis im Container
WORKDIR /usr/app/src

# Nur requirements kopieren → separates Layer, besserer Cache
COPY requirements.txt ./

# Abhängigkeiten ohne Pip-Cache installieren (kleineres Image)
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode nachziehen
COPY . .

# Startet FastAPI-App auf Port 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
