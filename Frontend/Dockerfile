###############################################################################
# 1️⃣  Build-Stage  – Flutter SDK-Image von cirruslabs
###############################################################################
FROM ghcr.io/cirruslabs/flutter:stable AS build

# Arbeitsverzeichnis im Container
WORKDIR /app

# ─────────────────────────────────────────────────────────────────────────────
# Copy-Strategie:
#   1) Nur pubspec-Dateien kopieren →  flutter pub get  (Cache bleibt erhalten)
#   2) Restliche Quellen kopieren    →  flutter build
# So werden Abhängigkeiten nur neu aufgelöst, wenn pubspec-Dateien sich ändern.
# ─────────────────────────────────────────────────────────────────────────────
COPY pubspec.* ./

# Alle Abhängigkeiten installieren (wird gecached)
RUN flutter pub get

# Jetzt erst den gesamten Source-Tree kopieren
COPY . .

# Release-Build als statisches Web (Standard-Ordner: build/web)
RUN flutter build web --release \
    --dart-define=FLUTTER_WEB_AUTO_DETECT=true \
    --web-renderer=canvaskit   # optional: schnellere Charts,  bessere Text-Rendering

###############################################################################
# 2️⃣  Runtime-Stage  – winziger NGINX-Alpine
###############################################################################
FROM nginx:alpine AS serve

# Statisches Build-Artefakt in NGINX-Document-Root kopieren
COPY --from=build /app/build/web /usr/share/nginx/html

# (Optional) eigenes NGINX-Config-Snippet einspielen, z. B. für CORS / Gzip
# COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Healthcheck (optional, z. B. in Kubernetes nützlich)
# HEALTHCHECK CMD wget -q --spider http://localhost || exit 1

CMD ["nginx", "-g", "daemon off;"]
