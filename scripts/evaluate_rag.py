"""
Script de evaluación RAGas para el pipeline RAG del bot de nutrición

Evalúa la calidad del sistema RAG usando métricas estándar:
- Faithfulness: ¿La respuesta es fiel al contexto recuperado?
- Answer Relevancy: ¿La respuesta es relevante a la pregunta?
- Context Precision: ¿El contexto recuperado es relevante?
- Context Recall: ¿Se recuperó toda la información necesaria?
- Answer Correctness: ¿La respuesta es correcta vs ground truth?

Uso:
    python scripts/evaluate_rag.py
"""

import os
import sys
import json
from datetime import datetime

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from datasets import Dataset
from ragas import evaluate
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="ragas")

from ragas.metrics.collections import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
)
from ragas.llms import LangchainLLMWrapper
from langchain_anthropic import ChatAnthropic

from services.rag_service import RAGService
from services.llm_service import get_response_with_context

# Configuración
EVAL_DATASET_PATH = "data/eval/eval_dataset.json"
EVAL_RESULTS_PATH = "data/eval/eval_results.json"
EVAL_CHART_PATH = "data/eval/eval_metrics.png"
EMBEDDINGS_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def load_eval_dataset(path: str) -> list:
    """Carga el dataset de evaluación desde JSON"""
    abs_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), path
    )
    with open(abs_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_rag_responses(eval_data: list, rag_service: RAGService) -> list:
    """
    Para cada pregunta del dataset, ejecuta el pipeline RAG completo:
    1. Busca contexto en FAISS
    2. Genera respuesta con Claude Haiku
    3. Retorna datos en formato RAGas

    Args:
        eval_data: Lista de dicts con 'question' y 'ground_truth'
        rag_service: Instancia de RAGService

    Returns:
        Lista de dicts con question, answer, contexts, ground_truth
    """
    results = []
    total = len(eval_data)

    for i, item in enumerate(eval_data, 1):
        question = item["question"]
        ground_truth = item["ground_truth"]

        print(f"  [{i}/{total}] {question[:60]}...")

        # 1. Buscar contexto RAG (k=3)
        rag_results = rag_service.search_knowledge(question, k=3)
        contexts = rag_results if rag_results else ["No se encontró información relevante."]

        # 2. Formatear contexto para el LLM
        rag_context = "\n\n".join(
            [f"[Fragmento {j}]\n{chunk}" for j, chunk in enumerate(contexts, 1)]
        )

        # 3. Generar respuesta con Claude Haiku
        answer = get_response_with_context(
            estado="active",
            user_message=question,
            rag_context=rag_context,
        )

        results.append(
            {
                "question": question,
                "answer": answer,
                "contexts": contexts,
                "ground_truth": ground_truth,
            }
        )

    return results


def create_ragas_dataset(rag_results: list) -> Dataset:
    """
    Convierte los resultados RAG al formato que espera RAGas

    RAGas espera:
    - user_input: str (pregunta)
    - response: str (respuesta del sistema)
    - retrieved_contexts: list[str] (contextos recuperados)
    - reference: str (ground truth)
    """
    ragas_data = {
        "user_input": [r["question"] for r in rag_results],
        "response": [r["answer"] for r in rag_results],
        "retrieved_contexts": [r["contexts"] for r in rag_results],
        "reference": [r["ground_truth"] for r in rag_results],
    }
    return Dataset.from_dict(ragas_data)


def run_evaluation(ragas_dataset: Dataset) -> dict:
    """
    Ejecuta la evaluación RAGas con Claude Haiku como evaluador

    Returns:
        EvaluationResult con scores por métrica
    """
    # Inicializar LLM evaluador (Claude Haiku - coste-efectivo)
    evaluator_llm = LangchainLLMWrapper(
        ChatAnthropic(
            model="claude-3-5-haiku-20241022",
            temperature=0,
            max_tokens=2048,
        )
    )

    # Inicializar embeddings (mismo modelo del proyecto)
    from langchain_huggingface import HuggingFaceEmbeddings
    evaluator_embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDINGS_MODEL,
        model_kwargs={"device": "cpu"},
    )

    # Métricas a evaluar
    metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        answer_correctness,
    ]

    # Ejecutar evaluación
    results = evaluate(
        dataset=ragas_dataset,
        metrics=metrics,
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
    )

    return results


def extract_metrics(results) -> dict:
    """Extrae las métricas agregadas del EvaluationResult via to_pandas()"""
    df = results.to_pandas()
    metric_cols = [
        c for c in df.columns
        if c not in ("user_input", "response", "retrieved_contexts", "reference")
    ]
    return {col: float(df[col].mean()) for col in metric_cols if df[col].dtype in ("float64", "float32")}


def save_results(results, rag_results: list, output_path: str):
    """Guarda los resultados de evaluación en JSON"""
    abs_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), output_path
    )

    metrics_dict = extract_metrics(results)

    output = {
        "timestamp": datetime.now().isoformat(),
        "metrics": {k: round(v, 4) for k, v in metrics_dict.items()},
        "num_questions": len(rag_results),
        "model_evaluated": "claude-3-5-haiku-20241022",
        "embeddings_model": EMBEDDINGS_MODEL,
        "detail": [],
    }

    # Añadir detalle por pregunta
    df = results.to_pandas()
    for idx, row in df.iterrows():
        detail_item = {"question": row.get("user_input", "")}
        for col in df.columns:
            if col not in ("user_input", "response", "retrieved_contexts", "reference"):
                val = row[col]
                if isinstance(val, float):
                    detail_item[col] = round(val, 4)
        output["detail"].append(detail_item)

    with open(abs_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n  Resultados guardados en: {output_path}")


def plot_metrics(results, output_path: str):
    """Genera gráfico de barras con las métricas"""
    try:
        import matplotlib.pyplot as plt

        metrics_dict = extract_metrics(results)

        if not metrics_dict:
            print("  No hay métricas numéricas para graficar")
            return

        names = list(metrics_dict.keys())
        values = list(metrics_dict.values())

        # Nombres más legibles
        display_names = [n.replace("_", " ").title() for n in names]

        plt.figure(figsize=(10, 6))
        bars = plt.barh(display_names, values, color="#4A90D9", edgecolor="#2C5F8A")

        for bar in bars:
            width = bar.get_width()
            plt.text(
                width + 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{width:.4f}",
                va="center",
                fontsize=10,
                fontweight="bold",
            )

        plt.xlabel("Score")
        plt.title("RAGas - Métricas de Evaluación del RAG")
        plt.xlim(0, 1.15)
        plt.tight_layout()

        abs_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), output_path
        )
        plt.savefig(abs_path, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"  Gráfico guardado en: {output_path}")

    except ImportError:
        print("  matplotlib no disponible, se omite el gráfico")


def main():
    print("=" * 60)
    print("  EVALUACIÓN RAGas DEL PIPELINE RAG")
    print("=" * 60)

    # Verificar API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n  Error: ANTHROPIC_API_KEY no configurada")
        sys.exit(1)

    # 1. Cargar dataset
    print("\n[1/5] Cargando dataset de evaluación...")
    eval_data = load_eval_dataset(EVAL_DATASET_PATH)
    print(f"  {len(eval_data)} preguntas cargadas")

    # 2. Inicializar RAG Service
    print("\n[2/5] Inicializando RAG Service...")
    rag_service = RAGService()

    # 3. Generar respuestas del pipeline RAG
    print("\n[3/5] Generando respuestas del pipeline RAG...")
    rag_results = generate_rag_responses(eval_data, rag_service)
    print(f"  {len(rag_results)} respuestas generadas")

    # 4. Crear dataset RAGas y evaluar
    print("\n[4/5] Ejecutando evaluación RAGas...")
    print("  (Esto puede tardar varios minutos...)")
    ragas_dataset = create_ragas_dataset(rag_results)
    results = run_evaluation(ragas_dataset)

    # 5. Mostrar resultados
    print("\n[5/5] Resultados:")
    print("-" * 40)
    metrics_dict = extract_metrics(results)
    for metric, score in metrics_dict.items():
        label = "OK" if score >= 0.7 else "BAJO"
        print(f"  [{label}] {metric}: {score:.4f}")
    print("-" * 40)

    # Guardar resultados
    save_results(results, rag_results, EVAL_RESULTS_PATH)
    plot_metrics(results, EVAL_CHART_PATH)

    print("\n" + "=" * 60)
    print("  EVALUACIÓN COMPLETADA")
    print("=" * 60)


if __name__ == "__main__":
    main()
