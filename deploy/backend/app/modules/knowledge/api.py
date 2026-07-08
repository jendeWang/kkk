from fastapi import APIRouter

router = APIRouter(prefix="/knowledge", tags=["知识图谱服务"])


@router.get("/health")
async def knowledge_health():
    return {"status": "healthy", "service": "knowledge-graph"}


@router.get("/query")
async def query_knowledge():
    return {"message": "知识图谱查询服务（预留接口）"}


@router.post("/rag/ask")
async def rag_ask():
    return {"message": "RAG问答服务（预留接口）"}