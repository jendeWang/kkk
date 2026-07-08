from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["AI推理服务"])


@router.get("/health")
async def ai_health():
    return {"status": "healthy", "service": "ai-inference"}


@router.post("/predict/disease")
async def predict_disease():
    return {"message": "AI推理服务模块（预留接口）"}