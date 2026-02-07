"""
RAG Service - Servicio de Retrieval Augmented Generation

Maneja la carga del vectorstore FAISS y búsqueda semántica en knowledge base
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
        self.vectorstore_path = vectorstore_path
        self.embeddings = self._load_embeddings()
        self.vectorstore = self._load_vectorstore()

    def _load_embeddings(self):
        """Carga el modelo de embeddings"""
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

    def _load_vectorstore(self) -> FAISS:
        """Carga el vectorstore FAISS desde disco"""
        if not os.path.exists(self.vectorstore_path):
            raise FileNotFoundError(f"Vectorstore no encontrado en: {self.vectorstore_path}")

        return FAISS.load_local(
            self.vectorstore_path,
            self.embeddings,
            allow_dangerous_deserialization=True
        )

    def search_knowledge(self, query: str, k: int = 3) -> List[str]:
        """
        Busca en la knowledge base

        Args:
            query: Pregunta del usuario
            k: Número de documentos a retornar

        Returns:
            Lista de chunks de texto relevantes
        """
        results = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in results]

    def augment_context(
        self,
        query: str,
        user_profile: Optional[Dict] = None,
        history: Optional[List] = None,
        k: int = 3
    ) -> Dict[str, str]:
        """
        Crea contexto enriquecido combinando RAG + perfil + historial

        Args:
            query: Pregunta del usuario
            user_profile: Perfil del usuario (opcional)
            history: Historial de conversación (opcional)
            k: Número de chunks de RAG a incluir

        Returns:
            Dict con user_context, history_context, rag_context
        """
        # RAG search
        rag_results = self.search_knowledge(query, k=k)

        # User context
        user_context = ""
        if user_profile:
            user_context = f"""Perfil del usuario:
- Peso: {user_profile.get('peso_kg')}kg
- Objetivo: {user_profile.get('objetivo')}
- Calorias objetivo: {user_profile.get('calorias_objetivo')} kcal/dia
- Macros: P:{user_profile.get('proteina_g')}g / C:{user_profile.get('carbos_g')}g / G:{user_profile.get('grasas_g')}g
"""

        # History context
        history_context = ""
        if history:
            history_context = "\n".join([
                f"{msg.get('role')}: {msg.get('content')}"
                for msg in history[-5:]
            ])

        # RAG context
        rag_context = "\n\n".join([
            f"[Info relevante {i}]\n{chunk}"
            for i, chunk in enumerate(rag_results, 1)
        ])

        return {
            "user_context": user_context,
            "history_context": history_context,
            "rag_context": rag_context
        }
