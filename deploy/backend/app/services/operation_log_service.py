from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Optional, Dict, Any
from datetime import datetime
from ..models.models import OperationLog, User


class OperationLogService:
    async def create_log(
        self,
        db: AsyncSession,
        user: User,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> OperationLog:
        """创建操作日志"""
        log = OperationLog(
            user_id=user.id,
            username=user.username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
            request_method=request_method,
            status=status,
            error_message=error_message,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    async def list_logs(
        self,
        db: AsyncSession,
        user_id: int,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """查询操作日志列表"""
        query = select(OperationLog).where(OperationLog.user_id == user_id)
        count_query = select(func.count(OperationLog.id)).where(OperationLog.user_id == user_id)

        if action:
            query = query.where(OperationLog.action == action)
            count_query = count_query.where(OperationLog.action == action)
        if resource_type:
            query = query.where(OperationLog.resource_type == resource_type)
            count_query = count_query.where(OperationLog.resource_type == resource_type)
        if status:
            query = query.where(OperationLog.status == status)
            count_query = count_query.where(OperationLog.status == status)
        if start_time:
            query = query.where(OperationLog.created_at >= start_time)
            count_query = count_query.where(OperationLog.created_at >= start_time)
        if end_time:
            query = query.where(OperationLog.created_at <= end_time)
            count_query = count_query.where(OperationLog.created_at <= end_time)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(desc(OperationLog.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        items = result.scalars().all()

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
        }


operation_log_service = OperationLogService()
