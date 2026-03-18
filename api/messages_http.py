from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from mysite.api.deps import get_db
from mysite.database.models import ChatRoom, Message
from mysite.database.schemas import MessageOut

router = APIRouter(prefix='/messages', tags=['Message'])


@router.get('/{group_id}', response_model=list[MessageOut])
async def get_messages(
    group_id: int,
    page: int = 1,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ChatRoom).where(ChatRoom.group_id == group_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail='Группа не найдена')

    offset = (page - 1) * limit
    msgs = await db.execute(
        select(Message)
        .where(
            Message.room_id == room.id,
            Message.is_deleted == False
        )
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    return msgs.scalars().all()