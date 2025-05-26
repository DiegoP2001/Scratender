from dotenv import load_dotenv

import urllib
import subprocess
import os
import requests


def install_google_chrome(version="stable"):
    """
    Descarga e instala Google Chrome en Ubuntu desde Python.
    version: 'stable', 'beta', o 'unstable' (dev)
    """
    url_map = {
        "stable": "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
        "beta": "https://dl.google.com/linux/direct/google-chrome-beta_current_amd64.deb",
        "unstable": "https://dl.google.com/linux/direct/google-chrome-unstable_current_amd64.deb"
    }

    url = url_map.get(version)
    if not url:
        print("❌ Versión inválida. Usa: stable, beta o unstable")
        return

    deb_path = "/tmp/google-chrome.deb"
    print(f"Descargando Chrome ({version})...")
    urllib.request.urlretrieve(url, deb_path)

    print("Instalando Chrome...")
    subprocess.run(["sudo", "dpkg", "-i", deb_path], check=True)
    subprocess.run(["sudo", "apt-get", "-f", "install", "-y"], check=True)  # resolver dependencias

    print("Chrome instalado correctamente.")


def get_installed_chrome_version():
    result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
    return result.stdout.strip()

def get_latest_stable_chrome_version():
    url = "https://chromiumdash.appspot.com/fetch_releases?channel=Stable&platform=Linux"
    response = requests.get(url)
    data = response.json()

    if data and isinstance(data, list):
        stables = [chrome for chrome in data if chrome["channel"] == "Stable"]
        return stables[0]["version"]
    return None


def is_chrome_outdated():
    local = get_installed_chrome_version()
    latest = get_latest_stable_chrome_version()

    local_version = local.split()[-1]
    if local_version != latest:
        print(f"Chrome está desactualizado: tienes {local_version}, hay {latest}")
        return True
    else:
        print(f"Chrome está actualizado: {local_version}")
        return False
