from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db, EvaluationResult
from app.models.schemas import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationMetrics
)
from app.services.evaluation import get_evaluation_service

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/", response_model=EvaluationResponse)
async def create_evaluation(
    request: EvaluationCreate,
    db: Session = Depends(get_db)
):
    """Create a new evaluation result."""
    try:
        evaluation_service = get_evaluation_service()

        evaluation = await evaluation_service.evaluate_query(
            db=db,
            query=request.query,
            retrieved_doc_ids=request.retrieved_doc_ids,
            user_feedback=request.user_feedback,
            expected_doc_ids=request.expected_doc_ids
        )

        return evaluation

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.post("/feedback")
async def submit_feedback(
    query: str,
    feedback: str,
    retrieved_doc_ids: List[int],
    db: Session = Depends(get_db)
):
    """Submit user feedback (thumbs up/down) for a query."""
    if feedback not in ["positive", "negative"]:
        raise HTTPException(status_code=400, detail="Feedback must be 'positive' or 'negative'")

    try:
        evaluation_service = get_evaluation_service()

        evaluation = await evaluation_service.evaluate_query(
            db=db,
            query=query,
            retrieved_doc_ids=retrieved_doc_ids,
            user_feedback=feedback
        )

        return {"message": "Feedback recorded", "evaluation_id": evaluation.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record feedback: {str(e)}")


@router.get("/metrics", response_model=EvaluationMetrics)
async def get_metrics(db: Session = Depends(get_db)):
    """Get aggregated evaluation metrics."""
    try:
        evaluation_service = get_evaluation_service()
        metrics = evaluation_service.get_aggregated_metrics(db)
        return metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/history", response_model=List[EvaluationResponse])
async def get_evaluation_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get evaluation history."""
    evaluations = db.query(EvaluationResult).order_by(
        EvaluationResult.created_at.desc()
    ).limit(limit).all()

    return evaluations
