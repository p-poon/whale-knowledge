from typing import List, Dict, Any, Optional
import logging
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import EvaluationResult
from app.services.embeddings import get_embedding_generator
from app.services.retrieval import get_retrieval_service

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for evaluating retrieval quality."""

    def __init__(self):
        self.embedding_generator = get_embedding_generator()
        self.retrieval_service = get_retrieval_service()

    async def evaluate_query(
        self,
        db: Session,
        query: str,
        retrieved_doc_ids: List[int],
        user_feedback: Optional[str] = None,
        expected_doc_ids: Optional[List[int]] = None
    ) -> EvaluationResult:
        """
        Evaluate a query and store results.

        Args:
            db: Database session
            query: Query text
            retrieved_doc_ids: List of retrieved document IDs
            user_feedback: Optional user feedback ('positive' or 'negative')
            expected_doc_ids: Optional ground truth document IDs

        Returns:
            EvaluationResult object
        """
        try:
            # Calculate semantic similarity if we have results
            semantic_similarity = None
            if retrieved_doc_ids:
                semantic_similarity = await self._calculate_semantic_similarity(
                    query, retrieved_doc_ids
                )

            # Calculate precision and recall if ground truth provided
            precision = None
            recall = None
            if expected_doc_ids and retrieved_doc_ids:
                precision, recall = self._calculate_precision_recall(
                    retrieved_doc_ids, expected_doc_ids
                )

            # Create evaluation record
            evaluation = EvaluationResult(
                query=query,
                retrieved_doc_ids=retrieved_doc_ids,
                semantic_similarity=semantic_similarity,
                user_feedback=user_feedback,
                expected_doc_ids=expected_doc_ids,
                precision=precision,
                recall=recall
            )

            db.add(evaluation)
            db.commit()
            db.refresh(evaluation)

            logger.info(f"Created evaluation for query: {query[:50]}...")
            return evaluation

        except Exception as e:
            logger.error(f"Error evaluating query: {e}")
            raise

    async def _calculate_semantic_similarity(
        self,
        query: str,
        doc_ids: List[int]
    ) -> Dict[str, float]:
        """
        Calculate semantic similarity scores.

        Args:
            query: Query text
            doc_ids: Document IDs

        Returns:
            Dictionary with similarity metrics
        """
        try:
            # For simplicity, return average score from retrieval
            # In production, this could be more sophisticated
            result = await self.retrieval_service.query(query, top_k=len(doc_ids))

            scores = [r["score"] for r in result["results"]]

            return {
                "avg_score": sum(scores) / len(scores) if scores else 0.0,
                "max_score": max(scores) if scores else 0.0,
                "min_score": min(scores) if scores else 0.0,
            }
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return {"avg_score": 0.0, "max_score": 0.0, "min_score": 0.0}

    def _calculate_precision_recall(
        self,
        retrieved: List[int],
        expected: List[int]
    ) -> tuple:
        """
        Calculate precision and recall.

        Args:
            retrieved: Retrieved document IDs
            expected: Expected (ground truth) document IDs

        Returns:
            Tuple of (precision, recall)
        """
        if not retrieved or not expected:
            return 0.0, 0.0

        retrieved_set = set(retrieved)
        expected_set = set(expected)

        # True positives: retrieved AND expected
        true_positives = len(retrieved_set & expected_set)

        # Precision: TP / (TP + FP) = TP / retrieved
        precision = true_positives / len(retrieved_set) if retrieved_set else 0.0

        # Recall: TP / (TP + FN) = TP / expected
        recall = true_positives / len(expected_set) if expected_set else 0.0

        return precision, recall

    def get_aggregated_metrics(self, db: Session) -> Dict[str, Any]:
        """
        Get aggregated evaluation metrics.

        Args:
            db: Database session

        Returns:
            Dictionary with aggregated metrics
        """
        evaluations = db.query(EvaluationResult).all()

        if not evaluations:
            return {
                "total_queries": 0,
                "avg_precision": None,
                "avg_recall": None,
                "avg_semantic_similarity": None,
                "positive_feedback_rate": None,
                "negative_feedback_rate": None,
            }

        # Calculate averages
        precisions = [e.precision for e in evaluations if e.precision is not None]
        recalls = [e.recall for e in evaluations if e.recall is not None]

        semantic_scores = []
        for e in evaluations:
            if e.semantic_similarity and isinstance(e.semantic_similarity, dict):
                avg = e.semantic_similarity.get("avg_score")
                if avg is not None:
                    semantic_scores.append(avg)

        # User feedback
        total_feedback = sum(1 for e in evaluations if e.user_feedback)
        positive_feedback = sum(1 for e in evaluations if e.user_feedback == "positive")
        negative_feedback = sum(1 for e in evaluations if e.user_feedback == "negative")

        return {
            "total_queries": len(evaluations),
            "avg_precision": sum(precisions) / len(precisions) if precisions else None,
            "avg_recall": sum(recalls) / len(recalls) if recalls else None,
            "avg_semantic_similarity": sum(semantic_scores) / len(semantic_scores) if semantic_scores else None,
            "positive_feedback_rate": positive_feedback / total_feedback if total_feedback else None,
            "negative_feedback_rate": negative_feedback / total_feedback if total_feedback else None,
        }


# Global evaluation service instance
def get_evaluation_service() -> EvaluationService:
    """Get evaluation service instance."""
    return EvaluationService()
