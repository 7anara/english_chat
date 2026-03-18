from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from mysite.api.deps import get_db
from mysite.database.models import ChatRoom
from mysite.database.schemas import RoomCreate, RoomOut, RoomDetailOut

router = APIRouter(prefix='/rooms', tags=['Group'])


@router.post('/', response_model=RoomOut)
async def create_room(data: RoomCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatRoom).where(ChatRoom.group_id == data.group_id)
    )
    room = result.scalar_one_or_none()
    if room:
        return room

    new_room = ChatRoom(
        group_id=data.group_id,
        group_name=data.group_name
    )
    db.add(new_room)
    await db.commit()
    await db.refresh(new_room)
    return new_room


@router.get('/', response_model=list[RoomOut])
async def get_rooms(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatRoom).where(ChatRoom.is_active == True)
    )
    return result.scalars().all()


@router.get('/{group_id}', response_model=RoomDetailOut)
async def get_room(group_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatRoom)
        .options(selectinload(ChatRoom.members))
        .where(ChatRoom.group_id == group_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail='Группа не найдена')
    return room


@router.delete('/{group_id}')
async def delete_room(group_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatRoom).where(ChatRoom.group_id == group_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail='Группа не найдена')
    await db.delete(room)
    await db.commit()
    return {'message': 'Группа удалена'}