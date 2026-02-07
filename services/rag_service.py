"""
RAG Service - Retrieval Augmented Generation

Motor RAG que integra el vectorstore FAISS existente con la conversación.
Proporciona búsqueda semántica y augmentación de contexto.
"""

import os
from typing import List, Dict, Optional
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


class RAGService:
    """
    Servicio de RAG para búsqueda semántica en knowledge base
    """

    def __init__(self, vectorstore_path: str = "data/vectorstore_faiss"):
        """
        Inicializa el servicio RAG

        Args:
            vectorstore_path: Ruta al directorio del vectorstore FAISS
        """
        self.vectorstore_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            vectorstore_path,
        )

        print(f"Vectorstore path: {self.vectorstore_path}")

        # Inicializar embeddings (mismo modelo usado para crear el vectorstore)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        print("✓ Embeddings inicializados")

        # Cargar vectorstore
        self.vectorstore = self.load_vectorstore()
        print("✓ Vectorstore cargado")

    def load_vectorstore(self) -> FAISS:
        """
        Carga el vectorstore FAISS desde disco

        Returns:
            Objeto FAISS vectorstore

        Raises:
            FileNotFoundError: Si el vectorstore no existe
        """
        if not os.path.exists(self.vectorstore_path):
            raise FileNotFoundError(
                f"Vectorstore no encontrado en {self.vectorstore_path}. "
                f"Ejecuta el notebook setup_rag.ipynb para crearlo."
            )

        try:
            vectorstore = FAISS.load_local(
                self.vectorstore_path,
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            return vectorstore
        except Exception as e:
            raise RuntimeError(f"Error al cargar vectorstore: {e}")

    def search_knowledge(self, query: str, k: int = 3) -> List[str]:
        """
        Busca documentos relevantes en la knowledge base

        Args:
            query: Query de búsqueda
            k: Número de documentos a retornar

        Returns:
            Lista de contenidos de documentos relevantes
        """
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            return [doc.page_content for doc in results]
        except Exception as e:
            print(f"Error en búsqueda RAG: {e}")
            return []

    def search_knowledge_with_scores(self, query: str, k: int = 3) -> List[tuple]:
        """
        Busca documentos con scores de similitud

        Args:
            query: Query de búsqueda
            k: Número de documentos a retornar

        Returns:
            Lista de tuplas (contenido, score)
        """
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            return [(doc.page_content, score) for doc, score in results]
        except Exception as e:
            print(f"Error en búsqueda con scores: {e}")
            return []

    def augment_context(
        self,
        query: str,
        user_profile: Optional[Dict] = None,
        history: Optional[List[Dict]] = None,
        k: int = 3,
    ) -> Dict[str, str]:
        """
        Crea contexto enriquecido para el LLM combinando RAG + user data + history

        Args:
            query: Query del usuario
            user_profile: Perfil del usuario (peso, objetivo, macros, etc.)
            history: Historial de conversación reciente
            k: Número de documentos RAG a incluir

        Returns:
            Dict con contexto estructurado:
                - user_context: Info del usuario
                - history_context: Historial de conversación
                - rag_context: Resultados de búsqueda RAG
                - query: Query original
        """
        # RAG search
        rag_results = self.search_knowledge(query, k=k)

        # User context
        user_context = ""
        if user_profile:
            user_context = f"""Perfil del usuario:
- Peso: {user_profile.get('peso_kg', 'N/A')}kg
- Objetivo: {user_profile.get('objetivo', 'N/A')}
- Calorías objetivo: {user_profile.get('calorias_objetivo', 'N/A')} kcal/día
- Macros diarios:
  • Proteína: {user_profile.get('proteina_g', 'N/A')}g
  • Carbohidratos: {user_profile.get('carbos_g', 'N/A')}g
  • Grasas: {user_profile.get('grasas_g', 'N/A')}g"""

        # History context (últimos mensajes)
        history_context = ""
        if history:
            history_messages = []
            for msg in history[-5:]:  # Últimos 5 mensajes
                role = msg.get("role", "user")
                content = msg.get("content", "")
                history_messages.append(f"{role}: {content}")
            history_context = "\n".join(history_messages)

        # RAG context
        rag_context = ""
        if rag_results:
            rag_chunks = []
            for i, chunk in enumerate(rag_results, 1):
                rag_chunks.append(f"[Fragmento {i}]\n{chunk}")
            rag_context = "\n\n".join(rag_chunks)

        return {
            "user_context": user_context,
            "history_context": history_context,
            "rag_context": rag_context,
            "query": query,
        }

    def format_augmented_prompt(self, augmented_context: Dict[str, str]) -> str:
        """
        Formatea el contexto augmentado en un prompt estructurado

        Args:
            augmented_context: Contexto augmentado de augment_context()

        Returns:
            Prompt formateado para incluir en el mensaje al LLM
        """
        parts = []

        if augmented_context.get("user_context"):
            parts.append(augmented_context["user_context"])

        if augmented_context.get("rag_context"):
            parts.append(
                f"\nInformación relevante de la guía de nutrición:\n{augmented_context['rag_context']}"
            )

        if augmented_context.get("history_context"):
            parts.append(
                f"\nHistorial de conversación reciente:\n{augmented_context['history_context']}"
            )

        if augmented_context.get("query"):
            parts.append(f"\nPregunta del usuario:\n{augmented_context['query']}")

        return "\n\n".join(parts)
