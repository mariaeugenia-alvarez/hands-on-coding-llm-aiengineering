"""
Script para inicializar el vectorstore FAISS desde cero

Este script:
1. Carga documentos markdown desde data/knowledge_base/
2. Los divide en chunks
3. Genera embeddings con HuggingFace
4. Crea índice FAISS
5. Guarda vectorstore en data/vectorstore_faiss/

Uso:
    python scripts/init_vectorstore.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar environment para evitar warnings
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
KNOWLEDGE_BASE_DIR = "data/knowledge_base"
VECTORSTORE_DIR = "data/vectorstore_faiss"


def load_documents(kb_dir: str) -> list:
    """
    Carga todos los documentos .md del directorio knowledge_base

    Args:
        kb_dir: Directorio con archivos markdown

    Returns:
        Lista de documentos cargados
    """

    kb_path = Path(kb_dir)
    if not kb_path.exists():
        print(f"Error: Ruta {kb_path} no existe")
        sys.exit(1)

    docs = []
    md_files = list(kb_path.glob('**/*.md'))  # Recursivo

    print(f"✓ {len(md_files)} archivos markdown encontrados")

    for md_file in md_files:
        print(f"  - {md_file.relative_to(kb_path)}")
        try:
            loader = TextLoader(str(md_file), encoding='utf-8')
            docs.extend(loader.load())
        except Exception as e:
            print(f"    Error al cargar {md_file.name}: {e}")

    print(f"✓ Total documentos cargados: {len(docs)}")
    return docs


def split_documents(documents: list, chunk_size: int, chunk_overlap: int) -> list:
    """
    Divide documentos en chunks

    Args:
        documents: Lista de documentos
        chunk_size: Tamaño del chunk
        chunk_overlap: Overlap entre chunks

    Returns:
        Lista de chunks
    """
    print(f"  - Chunk size: {chunk_size}")
    print(f"  - Overlap: {chunk_overlap}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = splitter.split_documents(documents)
    print(f"✓ {len(chunks)} chunks generados")

    return chunks


def create_vectorstore(chunks: list, embeddings) -> FAISS:
    """
    Crea vectorstore FAISS desde chunks

    Args:
        chunks: Lista de chunks de documentos
        embeddings: Modelo de embeddings

    Returns:
        Vectorstore FAISS
    """

    vectorstore = FAISS.from_documents(chunks, embeddings)

    print(f"  - Total vectores: {len(chunks)}")
    print(f"  - Dimensión embeddings: 384")

    return vectorstore


def save_vectorstore(vectorstore: FAISS, output_dir: str, metadata: dict):
    """
    Guarda vectorstore en disco

    Args:
        vectorstore: Vectorstore FAISS
        output_dir: Directorio de salida
        metadata: Metadata adicional
    """
    print("\nGuardando vectorstore en:", output_dir)

    # Crear directorio
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Guardar vectorstore
    vectorstore.save_local(output_dir)
    print("✓ Vectorstore guardado")

    # Guardar metadata
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print("✓ Metadata guardada")


def test_vectorstore(vectorstore: FAISS):
    """
    Prueba el vectorstore con queries de ejemplo

    Args:
        vectorstore: Vectorstore FAISS a probar
    """
    print("\nTesting RAG System...")

    queries = [
        '¿Cómo calcular las calorías de mantenimiento?',
        '¿Cuál es el factor para una actividad moderada?',
        'proteína por kilogramo de peso'
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n  Query {i}: {query}")
        results = vectorstore.similarity_search(query, k=2)

        if results:
            for j, result in enumerate(results, 1):
                content_preview = result.page_content[:150].replace('\n', ' ')
                print(f"    [{j}] {content_preview}...")
        else:
            print("    ⚠️  No se encontraron resultados")

    print("\n✓ RAG System funcionando correctamente")


def main():
    """Programa principal"""

    # Verificar que existe el directorio de knowledge base
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        print(f"\nError: Directorio {KNOWLEDGE_BASE_DIR} no existe")
        sys.exit(1)

    # Verificar que hay archivos .md
    md_files = list(Path(KNOWLEDGE_BASE_DIR).glob('**/*.md'))
    if not md_files:
        print(f"\nError: No se encontraron archivos .md en {KNOWLEDGE_BASE_DIR}")
        sys.exit(1)

    print(f"\nArchivos .md encontrados: {len(md_files)}")
    for md_file in md_files[:10]:  # Mostrar primeros 10
        print(f"  - {md_file.relative_to(KNOWLEDGE_BASE_DIR)}")
    if len(md_files) > 10:
        print(f"  ... y {len(md_files) - 10} más")

    # Preguntar si continuar
    response = input("\n¿Continuar con la inicialización? (s/n): ").strip().lower()
    if response != 's':
        print("Cancelado")
        sys.exit(0)

    try:
        # 1. Cargar documentos
        documents = load_documents(KNOWLEDGE_BASE_DIR)

        if not documents:
            print("\nNo se cargaron documentos")
            sys.exit(1)

        # 2. Dividir en chunks
        chunks = split_documents(documents, CHUNK_SIZE, CHUNK_OVERLAP)

        # 3. Inicializar embeddings
        print("\nInicializando modelo de embeddings...")
        print(f"  - Modelo: {EMBEDDINGS_MODEL}")
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDINGS_MODEL,
            model_kwargs={'device': 'cpu'}
        )
        print("✓ Embeddings inicializados")


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
            "documents": [str(Path(doc.metadata['source']).relative_to(KNOWLEDGE_BASE_DIR)) for doc in documents if 'source' in doc.metadata]
        }

        # 6. Guardar vectorstore
        save_vectorstore(vectorstore, VECTORSTORE_DIR, metadata)

        # 7. Probar vectorstore
        test_vectorstore(vectorstore)

        print("\n" + "=" * 60)
        print(" VECTORSTORE INICIALIZADO EXITOSAMENTE")
        print("=" * 60)
        print(f"\nResumen:")
        print(f"  - Documentos procesados: {len(documents)}")
        print(f"  - Chunks generados: {len(chunks)}")
        print(f"  - Ubicación: {VECTORSTORE_DIR}")
        print("\nEl RAG Service puede usar este vectorstore")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nError al inicializar vectorstore: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
