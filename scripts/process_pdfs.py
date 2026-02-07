"""
Script para procesar archivos PDF y agregarlos al knowledge base

Uso:
 1. Coloca tus PDFs en: data/knowledge_base/pdfs/
 2. Ejecuta: python scripts/process_pdfs.py
 3. Los PDFs se convertirán a .md en: data/knowledge_base/pdf_sources/
 4. Actualiza vectorstore: python scripts/update_vectorstore.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader

PDFS_INPUT_DIR = "data/knowledge_base/pdfs"
MARKDOWN_OUTPUT_DIR = "data/knowledge_base/pdf_sources"


def process_pdf(pdf_path: str, output_dir: str) -> bool:
    """
    Procesa un PDF y lo convierte a markdown

    Args:
        pdf_path: Ruta al archivo PDF
        output_dir: Directorio de salida para el markdown

    Returns:
        True si se procesó correctamente
    """
    pdf_name = Path(pdf_path).stem
    print(f"\n Procesando: {pdf_name}.pdf")

    try:
        # Cargar PDF con LangChain
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()

        print(f" {len(pages)} páginas encontradas")

        # Crear contenido markdown
        markdown_content = f"""# {pdf_name}

**Fuente:** {Path(pdf_path).name}
**Procesado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total de páginas:** {len(pages)}

---

"""

        # Agregar contenido de cada página
        for i, page in enumerate(pages, 1):
            content = page.page_content.strip()
            if content:  # Solo agregar páginas con contenido
                markdown_content += f"\n## Página {i}\n\n{content}\n\n---\n"

        # Guardar markdown
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{pdf_name}.md")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f" Guardado en: {output_path}")
        return True

    except Exception as e:
        print(f" Error al procesar {pdf_name}: {e}")
        return False


def find_pdfs(directory: str) -> list:
    """
    Encuentra todos los PDFs en un directorio

    Args:
        directory: Directorio a buscar

    Returns:
        Lista de rutas a PDFs
    """
    if not os.path.exists(directory):
        return []

    pdf_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))

    return pdf_files


def main():
    """Programa principal"""
    print("=" * 60)
    print(" PROCESADOR DE PDFs - Knowledge Base")
    print("=" * 60)

    # Verificar que existe el directorio de PDFs
    if not os.path.exists(PDFS_INPUT_DIR):
        print(f"\n Directorio {PDFS_INPUT_DIR} no existe")
        print("\nCreando directorio...")
        os.makedirs(PDFS_INPUT_DIR, exist_ok=True)
        print(f" Directorio creado: {PDFS_INPUT_DIR}")
        print("\n Instrucciones:")
        print(" 1. Coloca tus archivos PDF en ese directorio")
        print(" 2. Ejecuta este script nuevamente")
        print(" 3. Los PDFs se convertirán a markdown")
        print(" 4. Ejecuta: python scripts/update_vectorstore.py")
        return

    # Buscar PDFs
    pdf_files = find_pdfs(PDFS_INPUT_DIR)

    if not pdf_files:
        print(f"\n No se encontraron archivos PDF en {PDFS_INPUT_DIR}")
        print("\n Instrucciones:")
        print(" 1. Coloca archivos PDF en el directorio")
        print(" 2. Tipos recomendados:")
        print(" - Guías de nutrición deportiva")
        print(" - Papers científicos sobre suplementos")
        print(" - Manuales de entrenamiento")
        print(" - Libros de recetas")
        return

    # Mostrar PDFs encontrados
    print(f"\n📚 PDFs encontrados: {len(pdf_files)}")
    for i, pdf in enumerate(pdf_files, 1):
        pdf_name = Path(pdf).name
        size_mb = os.path.getsize(pdf) / (1024 * 1024)
        print(f" {i}. {pdf_name} ({size_mb:.2f} MB)")

    # Confirmar
    response = input("\n¿Procesar estos PDFs? (s/n): ").strip().lower()
    if response != 's':
        print(" Cancelado")
        return

    # Procesar cada PDF
    print("\n" + "=" * 60)
    print(" PROCESANDO PDFs")
    print("=" * 60)

    success_count = 0
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n--- [{i}/{len(pdf_files)}] ---")
        if process_pdf(pdf_path, MARKDOWN_OUTPUT_DIR):
            success_count += 1

    # Resumen
    print("\n" + "=" * 60)
    if success_count > 0:
        print(f" {success_count}/{len(pdf_files)} PDFs procesados")
        print("=" * 60)
        print(f"\n Archivos markdown guardados en: {MARKDOWN_OUTPUT_DIR}")
        print("\n Siguiente paso:")
        print(" python scripts/update_vectorstore.py")
        print("\nEsto actualizará el vectorstore con el contenido de los PDFs.")
    else:
        print(" No se procesó ningún PDF")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Cancelado por el usuario")
        sys.exit(0)
