from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from mysite.api.deps import get_db
from mysite.database.models import Message
from mysite.database.schemas import MessageEdit, MessageOut

router = APIRouter(prefix='/messages', tags=['MessageEdit'])


@router.patch('/{message_id}/edit', response_model=MessageOut)
async def edit_message(
    message_id: int,
    data: MessageEdit,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail='Сообщение не найдено')
    if message.is_deleted:
        raise HTTPException(status_code=400, detail='Сообщение удалено')

    message.text = data.text
    message.edited_at = datetime.utcnow()
    await db.commit()
    await db.refresh(message)
    return message


@router.delete('/{message_id}')
async def delete_message(
    message_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail='Сообщение не найдено')

    message.is_deleted = True
    message.text = 'Сообщение удалено'
    await db.commit()
    return {'message': 'Сообщение удалено'}