"""
Script para actualizar el vectorstore FAISS con nuevos documentos

Uso:
 python scripts/update_vectorstore.py
"""

import os
import sys
import json
from datetime import datetime

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


# Configuración
KNOWLEDGE_BASE_DIR = "data/knowledge_base"
VECTORSTORE_DIR = "data/vectorstore_faiss"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_documents(directory: str) -> list:
    """
    Carga todos los documentos .md del directorio

    Args:
        directory: Directorio con archivos markdown

    Returns:
        Lista de documentos cargados
    """
    print(f"\n Cargando documentos desde: {directory}")

    # Cargar todos los .md recursivamente
    loader = DirectoryLoader(
        directory,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    documents = loader.load()
    print(f" {len(documents)} documentos encontrados")

    # Mostrar lista de documentos
    for doc in documents:
        filename = os.path.basename(doc.metadata["source"])
        print(f" - {filename}")

    return documents


def split_documents(documents: list) -> list:
    """
    Divide documentos en chunks

    Args:
        documents: Lista de documentos

    Returns:
        Lista de chunks
    """
    print(f"\n Dividiendo documentos en chunks...")
    print(f" Chunk size: {CHUNK_SIZE}")
    print(f" Overlap: {CHUNK_OVERLAP}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", " ", ""],
    )

    chunks = text_splitter.split_documents(documents)
    print(f" {len(chunks)} chunks generados")

    return chunks


def create_vectorstore(chunks: list, embeddings) -> FAISS:
    """
    Crea un nuevo vectorstore desde chunks

    Args:
        chunks: Lista de chunks de documentos
        embeddings: Modelo de embeddings

    Returns:
        Vectorstore FAISS
    """
    print(f"\n Creando vectorstore FAISS...")

    vectorstore = FAISS.from_documents(chunks, embeddings)

    print(f" Vectorstore creado con {len(chunks)} chunks")

    return vectorstore


def save_vectorstore(vectorstore: FAISS, output_dir: str, metadata: dict):
    """
    Guarda el vectorstore en disco

    Args:
        vectorstore: Vectorstore FAISS
        output_dir: Directorio de salida
        metadata: Metadata adicional
    """
    print(f"\n Guardando vectorstore en: {output_dir}")

    # Crear directorio si no existe
    os.makedirs(output_dir, exist_ok=True)

    # Guardar vectorstore
    vectorstore.save_local(output_dir)
    print(f" Vectorstore guardado")

    # Guardar metadata
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f" Metadata guardada")


def main():
    """Programa principal"""
    print("=" * 60)
    print(" ACTUALIZACIÓN DE VECTORSTORE FAISS")
    print("=" * 60)

    # Verificar que existe el directorio de knowledge base
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        print(f"\n Error: Directorio {KNOWLEDGE_BASE_DIR} no existe")
        print("Crea el directorio y agrega archivos .md")
        sys.exit(1)

    # Verificar que hay archivos .md
    md_files = []
    for root, dirs, files in os.walk(KNOWLEDGE_BASE_DIR):
        md_files.extend([f for f in files if f.endswith(".md")])

    if not md_files:
        print(f"\n Error: No se encontraron archivos .md en {KNOWLEDGE_BASE_DIR}")
        print("Agrega al menos un archivo .md")
        sys.exit(1)

    print(f"\n Archivos .md encontrados: {len(md_files)}")

    # Preguntar si continuar
    response = input("\n¿Continuar con la actualización? (s/n): ").strip().lower()
    if response != "s":
        print(" Cancelado")
        sys.exit(0)

    try:
        # 1. Cargar documentos
        documents = load_documents(KNOWLEDGE_BASE_DIR)

        if not documents:
            print("\n No se cargaron documentos")
            sys.exit(1)

        # 2. Dividir en chunks
        chunks = split_documents(documents)

        # 3. Inicializar embeddings
        print(f"\n Inicializando modelo de embeddings...")
        print(f" Modelo: {EMBEDDINGS_MODEL}")
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDINGS_MODEL, model_kwargs={"device": "cpu"}
        )
        print(" Embeddings inicializados")

        # 4. Crear vectorstore
        vectorstore = create_vectorstore(chunks, embeddings)

        # 5. Preparar metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "embeddings_provider": "huggingface",
            "model": EMBEDDINGS_MODEL,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "total_chunks": len(chunks),
            "total_docs": len(documents),
            "documents": [
                os.path.basename(doc.metadata["source"]) for doc in documents
            ],
        }

        # 6. Guardar vectorstore
        save_vectorstore(vectorstore, VECTORSTORE_DIR, metadata)

        print("\n" + "=" * 60)
        print(" VECTORSTORE ACTUALIZADO EXITOSAMENTE")
        print("=" * 60)
        print(f"\n Resumen:")
        print(f" - Documentos procesados: {len(documents)}")
        print(f" - Chunks generados: {len(chunks)}")
        print(f" - Ubicación: {VECTORSTORE_DIR}")
        print("\n El RAG Service ahora usará estos documentos")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n Error al actualizar vectorstore: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
