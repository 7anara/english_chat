from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from mysite.api.deps import get_db
from mysite.database.models import ChatRoom, ReadState
from mysite.database.schemas import ReadStateOut

router = APIRouter(prefix='/messages', tags=['ReadMessage'])


@router.patch('/{group_id}/read')
async def mark_as_read(
    group_id: int,
    email: str,
    last_message_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ChatRoom).where(ChatRoom.group_id == group_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail='Группа не найдена')

    state = await db.execute(
        select(ReadState).where(
            ReadState.room_id == room.id,
            ReadState.email == email
        )
    )
    state = state.scalar_one_or_none()

    if state:
        state.last_read_message_id = last_message_id
        state.unread_count = 0
        state.updated_at = datetime.utcnow()
    else:
        db.add(ReadState(
            room_id=room.id,
            email=email,
            last_read_message_id=last_message_id,
            unread_count=0
        ))
    await db.commit()
    return {'message': 'Прочитано'}


@router.get('/{group_id}/read-state', response_model=ReadStateOut)
async def get_read_state(
    group_id: int,
    email: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ChatRoom).where(ChatRoom.group_id == group_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail='Группа не найдена')

    state = await db.execute(
        select(ReadState).where(
            ReadState.room_id == room.id,
            ReadState.email == email
        )
    )
    state = state.scalar_one_or_none()
    if not state:
        raise HTTPException(status_code=404, detail='Статус не найден')
    return state