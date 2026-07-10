from fastapi import APIRouter

router = APIRouter(prefix="/agents", tags=["多智能体服务"])


@router.get("/health")
async def agents_health():
    return {"status": "healthy", "service": "multi-agent"}


@router.get("/")
async def get_agents():
    return {
        "agents": [
            {"id": "weather", "name": "气象Agent", "status": "running", "description": "环境监测与预警"},
            {"id": "disease", "name": "病虫害Agent", "status": "running", "description": "AI识别+防治建议"},
            {"id": "control", "name": "调控Agent", "status": "running", "description": "设备调度与控制"},
        ]
    }


@router.get("/{agent_id}/status")
async def get_agent_status(agent_id: str):
    return {"agent_id": agent_id, "status": "online", "last_active": "2026-07-07T10:00:00Z"}


@router.post("/{agent_id}/invoke")
async def invoke_agent(agent_id: str):
    return {"agent_id": agent_id, "result": "智能体服务模块（预留接口）"}