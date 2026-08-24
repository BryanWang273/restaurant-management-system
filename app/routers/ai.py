from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ai_recommendation import InventoryRecommendationResponse
from app.services import ai_recommendation_service

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/inventory-recommendations", response_model=InventoryRecommendationResponse)
def get_inventory_recommendations(db: Session = Depends(get_db)):
    try:
        return ai_recommendation_service.generate_recommendations(db)
    except ai_recommendation_service.AIRecommendationConfigError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ai_recommendation_service.AIRecommendationUpstreamError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ai_recommendation_service.AIRecommendationError as e:
        raise HTTPException(status_code=500, detail=str(e))
