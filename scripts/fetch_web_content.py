"""
Script para descargar contenido web y agregarlo al knowledge base

Uso:
 python scripts/fetch_web_content.py
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KNOWLEDGE_BASE_DIR = "data/knowledge_base"
WEB_CONTENT_DIR = os.path.join(KNOWLEDGE_BASE_DIR, "web_sources")


def fetch_url(url: str) -> tuple:
    """
    Descarga contenido de una URL

    Args:
        url: URL a descargar

    Returns:
        Tupla (título, contenido_texto)
    """
    print(f"\nDescargando: {url}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extraer título
        title = soup.find("h1")
        title = title.get_text().strip() if title else "Sin título"

        # Remover scripts, styles, etc.
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Extraer texto
        text = soup.get_text()

        # Limpiar texto
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
        text = "\n".join(chunk for chunk in chunks if chunk)

        print(f" Descargado: {len(text)} caracteres")

        return title, text

    except Exception as e:
        print(f" Error al descargar {url}: {e}")
        return None, None


def save_to_markdown(url: str, title: str, content: str, output_dir: str):
    """
    Guarda contenido web como markdown

    Args:
        url: URL original
        title: Título del contenido
        content: Contenido de texto
        output_dir: Directorio de salida
    """
    os.makedirs(output_dir, exist_ok=True)

    # Crear nombre de archivo seguro
    filename = title.replace(" ", "_").replace("/", "_")[:50]
    filename = f"{filename}.md"
    filepath = os.path.join(output_dir, filename)

    # Crear contenido markdown
    markdown_content = f"""# {title}

**Fuente:** {url}
**Descargado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{content}

---

*Nota: Este contenido fue descargado automáticamente de la web. Verifica la fuente original para información actualizada.*
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    print(f" Guardado en: {filepath}")


def main():
    """Programa principal"""
    urls = [
        # Ejemplo:
        "https://www.fitnessrevolucionario.com/2017/07/22/triaje-de-nutrientes-deficiencias-y-riesgos-suplementacion/",
        "https://www.fitnessrevolucionario.com/2019/03/23/comida-real-despues-de-entrenar/",
        "https://www.fitnessrevolucionario.com/2013/04/07/lo-que-siempre-quisiste-saber-sobre-la-proteina-de-suero/",
        "https://www.fitnessrevolucionario.com/2015/04/26/creatina-uno-de-los-mejores-suplementos-beneficios-usos-dosis-riesgos/",
        "https://www.fitnessrevolucionario.com/2018/02/21/cafeina-rendimiento-perdida-grasa/",
    ]

    if not urls:
        print("\n No hay URLs configuradas.")
        return

    print(f"\n URLs a descargar: {len(urls)}")
    for i, url in enumerate(urls, 1):
        print(f" {i}. {url}")

    response = input("\n¿Continuar? (s/n): ").strip().lower()
    if response != "s":
        print("Cancelado")
        return

    # Crear directorio de salida
    os.makedirs(WEB_CONTENT_DIR, exist_ok=True)

    # Descargar cada URL
    success_count = 0
    for i, url in enumerate(urls, 1):
        print(f"\n--- [{i}/{len(urls)}] ---")
        title, content = fetch_url(url)

        if title and content:
            save_to_markdown(url, title, content, WEB_CONTENT_DIR)
            success_count += 1

    print("\n" + "=" * 60)
    if success_count > 0:
        print(f" {success_count}/{len(urls)} URLs descargadas")
        print("=" * 60)
        print(f"\nArchivos guardados en: {WEB_CONTENT_DIR}")
        print("\n Siguiente paso:")
        print(" python scripts/update_vectorstore.py")
        print("\nEsto actualizará el vectorstore con el nuevo contenido.")
    else:
        print(" No se descargó ningún contenido")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Cancelado por el usuario")
        sys.exit(0)
