from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from mysite.api.deps import get_db
from mysite.database.models import ChatRoom, Member
from mysite.database.schemas import MemberCreate, MemberOut

router = APIRouter(prefix='/rooms', tags=['Members'])


@router.post('/{group_id}/members/', response_model=MemberOut)
async def add_member(
    group_id: int,
    data: MemberCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ChatRoom).where(ChatRoom.group_id == group_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail='Группа не найдена')

    existing = await db.execute(
        select(Member).where(
            Member.room_id == room.id,
            Member.email == data.email
        )
    )
    member = existing.scalar_one_or_none()
    if member:
        return member

    new_member = Member(
        room_id=room.id,
        email=data.email,
        full_name=data.full_name,
        is_teacher=data.is_teacher
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    return new_member


@router.get('/{group_id}/members/', response_model=list[MemberOut])
async def get_members(group_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatRoom).where(ChatRoom.group_id == group_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail='Группа не найдена')

    members = await db.execute(
        select(Member).where(Member.room_id == room.id)
    )
    return members.scalars().all()


@router.delete('/{group_id}/members/{email}')
async def remove_member(
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

    member = await db.execute(
        select(Member).where(
            Member.room_id == room.id,
            Member.email == email
        )
    )
    member = member.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail='Участник не найден')

    await db.delete(member)
    await db.commit()
    return {'message': 'Участник удалён'}