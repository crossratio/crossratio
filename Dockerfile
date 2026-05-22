# Image de base légère
FROM python:3.11-slim

# Définit le répertoire de travail
WORKDIR /app

# Copie les fichiers nécessaires
COPY requirements.txt .
COPY check_ratio.py .
COPY .env .

# Installe les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installe cron pour les tâches planifiées
RUN apt-get update && \
    apt-get install -y cron && \
    rm -rf /var/lib/apt/lists/*

# Copie la configuration cron
COPY cronjob /etc/cron.d/torrent-ratio-notifier

# Donne les permissions nécessaires
RUN chmod 0644 /etc/cron.d/torrent-ratio-notifier && \
    chmod +x /app/check_ratio.py && \
    touch /var/log/cron.log

# Active le cron (exécute en premier plan)
CMD ["cron", "-f"]