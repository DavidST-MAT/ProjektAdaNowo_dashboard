# Verwenden Sie das offizielle Python-Image als Basis
FROM python:3.10

# Arbeitsverzeichnis setzen
WORKDIR /Dashboard

# Kopieren Sie die Abhängigkeiten und installieren Sie sie
COPY requirements.txt dfe
RUN pip install --no-cache-dir -r requirements.txt

# Installiere Gunicorn
RUN pip install gunicorn

# Kopieren Sie den Rest der Anwendung
COPY . /Dashboard/

# Gunicorn starten und Nginx konfigurieren
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "Dashboard.wsgi:application"] 
