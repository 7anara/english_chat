from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from mysite.api.deps import get_db
from mysite.database.models import ChatRoom, Message, Member, ReadState
from mysite.database.schemas import WSMessageIn
import json

router = APIRouter(tags=['WebSocket'])

active_connections: dict[int, dict[str, WebSocket]] = {}


async def connect(room_id: int, email: str, ws: WebSocket):
    await ws.accept()
    if room_id not in active_connections:
        active_connections[room_id] = {}
    active_connections[room_id][email] = ws


def disconnect(room_id: int, email: str):
    if room_id in active_connections:
        active_connections[room_id].pop(email, None)
        if not active_connections[room_id]:
            del active_connections[room_id]


async def broadcast(room_id: int, data: dict):
    if room_id not in active_connections:
        return

    dead_connections = []

    for email, ws in active_connections[room_id].items():
        try:
            await ws.send_text(
                json.dumps(data, ensure_ascii=False, default=str)
            )
        except Exception:
            dead_connections.append(email)

    for email in dead_connections:
        active_connections[room_id].pop(email, None)

    if not active_connections[room_id]:
        del active_connections[room_id]


async def update_member_status(
    room_id: int, email: str,
    is_online: bool, db: AsyncSession
):
    result = await db.execute(
        select(Member).where(
            Member.room_id == room_id,
            Member.email == email
        )
    )
    member = result.scalar_one_or_none()
    if member:
        member.is_online = is_online
        member.last_seen = datetime.utcnow()
        await db.commit()


@router.websocket('/ws/{group_id}')
async def websocket_chat(
    websocket: WebSocket,
    group_id: int,
    email: str,
    name: str,
    is_teacher: bool = False,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ChatRoom).where(ChatRoom.group_id == group_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        await websocket.close(code=4004)
        return

    await connect(room.id, email, websocket)
    await update_member_status(room.id, email, True, db)

    await broadcast(room.id, {
        'type': 'online',
        'online_count': len(active_connections.get(room.id, {}))
    })

    await broadcast(room.id, {
        'type': 'system',
        'text': f'{name} вошёл в чат'
    })

    try:
        while True:
            data = await websocket.receive_text()
            msg = WSMessageIn(**json.loads(data))

            if msg.type == 'typing':
                await broadcast(room.id, {
                    'type': 'typing',
                    'sender_name': name,
                    'sender_email': email
                })

            elif msg.type == 'read' and msg.text:
                state = await db.execute(
                    select(ReadState).where(
                        ReadState.room_id == room.id,
                        ReadState.email == email
                    )
                )
                state = state.scalar_one_or_none()
                if state:
                    state.last_read_message_id = int(msg.text)
                    state.unread_count = 0
                    state.updated_at = datetime.utcnow()
                else:
                    db.add(ReadState(
                        room_id=room.id,
                        email=email,
                        last_read_message_id=int(msg.text),
                        unread_count=0
                    ))
                await db.commit()
                await broadcast(room.id, {
                    'type': 'read',
                    'sender_email': email,
                    'last_read_message_id': int(msg.text)
                })

            elif msg.type == 'message' and msg.text:
                new_msg = Message(
                    room_id=room.id,
                    sender_email=email,
                    sender_name=name,
                    is_teacher=is_teacher,
                    text=msg.text
                )
                db.add(new_msg)
                await db.commit()
                await db.refresh(new_msg)

                members = await db.execute(
                    select(Member).where(
                        Member.room_id == room.id,
                        Member.email != email
                    )
                )
                for member in members.scalars().all():
                    state = await db.execute(
                        select(ReadState).where(
                            ReadState.room_id == room.id,
                            ReadState.email == member.email
                        )
                    )
                    state = state.scalar_one_or_none()
                    if state:
                        state.unread_count += 1
                        state.updated_at = datetime.utcnow()
                    else:
                        db.add(ReadState(
                            room_id=room.id,
                            email=member.email,
                            unread_count=1
                        ))
                await db.commit()

                await broadcast(room.id, {
                    'type': 'message',
                    'id': new_msg.id,
                    'room_id': room.id,
                    'sender_email': new_msg.sender_email,
                    'sender_name': new_msg.sender_name,
                    'is_teacher': new_msg.is_teacher,
                    'text': new_msg.text,
                    'is_deleted': new_msg.is_deleted,
                    'edited_at': None,
                    'created_at': str(new_msg.created_at),
                    'attachments': []
                })

    except WebSocketDisconnect:
        disconnect(room.id, email)
        await update_member_status(room.id, email, False, db)
        await broadcast(room.id, {
            'type': 'online',
            'online_count': len(active_connections.get(room.id, {}))
        })
        await broadcast(room.id, {
            'type': 'system',
            'text': f'{name} вышел из чата'
        })