import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import json
import logging

# Configure les logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Charge les variables d'environnement
load_dotenv()

# Configuration ntfy
NTFY_TOPIC = os.getenv("NTFY_TOPIC")
NTFY_TOKEN = os.getenv("NTFY_TOKEN")
NTFY_TLD = os.getenv("NTFY_TLD")
NTFY_URL = f"https://{NTFY_TLD}/{NTFY_TOPIC}"

# Charge la configuration des sites depuis .env
SITES_CONFIG = json.loads(os.getenv("SITES_CONFIG", "{}"))

def get_ratio(site_name, site_config):
    try:
        if site_config.get("api"):
            return get_ratio_from_api(site_name, site_config)
        else:
            return get_ratio_from_scraping(site_name, site_config)
    except Exception as e:
        logger.error(f"Erreur pour {site_name}: {str(e)}")
        return f"Erreur: {str(e)}"

def get_ratio_from_scraping(site_name, site_config):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(
        site_config["url"],
        headers=headers,
        cookies=site_config.get("auth", {}).get("cookies"),
        timeout=10
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    selector = site_config["selector"].replace(":contains", ":-soup-contains")
    ratio_element = soup.select_one(selector)
    if ratio_element:
        return ratio_element.get_text(strip=True)
    else:
        return "Non trouvé"

def get_ratio_from_api(site_name, site_config):
    headers = site_config.get("auth", {}).get("headers", {})
    if "User-Agent" not in headers:
        headers["User-Agent"] = "Mozilla/5.0"

    try:
        response = requests.get(
            site_config["url"],
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        uploaded = data.get(site_config.get("uploaded_key", "total_uploaded_bytes"), 0)
        downloaded = data.get(site_config.get("downloaded_key", "total_downloaded_bytes"), 0)
        
        if not isinstance(uploaded, (int, float)) or not isinstance(downloaded, (int, float)):
            return "Données invalides"

        if downloaded > 0 and uploaded is not None:
            ratio = uploaded / downloaded
            return f"{ratio:.3f}"
        else:
            return "∞" if uploaded > 0 else "Non trouvé"

    except Exception as e:
        logger.error(f"Erreur API pour {site_name}: {str(e)}")
        return f"Erreur API: {str(e)}"

def send_ntfy_notification(message):
    headers = {
        "Authorization": f"Bearer {NTFY_TOKEN}",
        "Title": "Ratio Torrent Hebdomadaire",  # Emoji dans le titre
        "Tags": "torrent,ratio",
        "Priority": "3",
        "Content-Type": "text/markdown"  # Active le Markdown
    }
    try:
        response = requests.post(
            NTFY_URL,
            headers=headers,
#            json=payload,
            data=message,
            timeout=10
        )
        response.raise_for_status()
        logger.info("Notification envoyée avec succès !")
    except Exception as e:
        logger.error(f"Erreur ntfy: {str(e)}")

def main():
    logger.info("Début de la vérification des ratios...")
    results = []
    for site_name, config in SITES_CONFIG.items():
        ratio = get_ratio(site_name, config)
        results.append(f"- **{site_name}**: `{ratio}`")  # Affiche le ratio en code
    message = "\n".join(results)
    send_ntfy_notification(message)

if __name__ == "__main__":
    main()
