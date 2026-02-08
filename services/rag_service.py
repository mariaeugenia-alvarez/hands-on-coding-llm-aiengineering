"""
RAG Service - Retrieval Augmented Generation

Motor RAG que integra el vectorstore FAISS existente con la conversación.
Proporciona búsqueda semántica con reranking por CrossEncoder.

Pipeline: Query → FAISS (top N candidatos) → CrossEncoder rerank → top K resultados
"""

import os
from typing import List, Dict, Optional
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from sentence_transformers import CrossEncoder

# Modelo CrossEncoder multilingüe para reranking (entrenado en mMARCO)
RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


class RAGService:
    """
    Servicio de RAG para búsqueda semántica en knowledge base
    con reranking por CrossEncoder para mejorar la precisión.
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
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={"device": "cpu"},
        )
        print("✓ Embeddings inicializados")

        # Inicializar CrossEncoder para reranking
        self.reranker = CrossEncoder(RERANKER_MODEL)
        print(f"✓ Reranker inicializado ({RERANKER_MODEL})")

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

    def _rerank(self, query: str, documents: list, top_k: int) -> list:
        """
        Reordena documentos usando CrossEncoder para mejorar la relevancia.

        El CrossEncoder evalúa la relevancia de cada par (query, documento)
        de forma independiente, lo que es más preciso que la similitud coseno
        de los embeddings bi-encoder.

        Args:
            query: Query original del usuario
            documents: Lista de objetos Document de LangChain
            top_k: Número de documentos a devolver tras reranking

        Returns:
            Lista de documentos reordenados (top_k mejores)
        """
        if not documents:
            return []

        # Crear pares (query, documento) para el CrossEncoder
        pairs = [(query, doc.page_content) for doc in documents]

        # Obtener scores de relevancia del CrossEncoder
        scores = self.reranker.predict(pairs)

        # Emparejar documentos con sus scores y ordenar por relevancia
        scored_docs = sorted(
            zip(documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        reranked = [doc for doc, score in scored_docs[:top_k]]

        print(f"    Rerank: {len(documents)} candidatos → {len(reranked)} seleccionados")
        return reranked

    def search_knowledge(self, query: str, k: int = 3) -> List[str]:
        """
        Busca documentos relevantes con retrieve + rerank.

        Pipeline: FAISS top k*3 → CrossEncoder rerank → top k

        Args:
            query: Query de búsqueda
            k: Número de documentos finales a retornar

        Returns:
            Lista de contenidos de documentos relevantes (rerankeados)
        """
        try:
            # Recuperar más candidatos para que el reranker tenga margen
            candidates = self.vectorstore.similarity_search(query, k=k * 3)

            # Reranking con CrossEncoder
            reranked = self._rerank(query, candidates, top_k=k)

            return [doc.page_content for doc in reranked]
        except Exception as e:
            print(f"Error en búsqueda RAG: {e}")
            return []

    def search_knowledge_with_scores(self, query: str, k: int = 3) -> List[tuple]:
        """
        Busca documentos con scores de relevancia (post-reranking).

        Args:
            query: Query de búsqueda
            k: Número de documentos a retornar

        Returns:
            Lista de tuplas (contenido, score_reranker)
        """
        try:
            candidates = self.vectorstore.similarity_search(query, k=k * 3)

            if not candidates:
                return []

            pairs = [(query, doc.page_content) for doc in candidates]
            scores = self.reranker.predict(pairs)

            scored = sorted(
                zip(candidates, scores),
                key=lambda x: x[1],
                reverse=True,
            )

            return [
                (doc.page_content, float(score))
                for doc, score in scored[:k]
            ]
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
