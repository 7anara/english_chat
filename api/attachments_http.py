from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from mysite.api.deps import get_db
from mysite.database.models import Message, Attachment
from mysite.database.schemas import AttachmentOut
import os
import uuid

router = APIRouter(prefix='/attachments', tags=['Attachments'])

UPLOAD_DIR = 'media'


@router.post('/{message_id}', response_model=AttachmentOut)
async def upload_attachment(
    message_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail='Сообщение не найдено')

    mime = file.content_type or 'application/octet-stream'
    if mime.startswith('image'):
        file_type = 'image'
        folder = 'images'
    elif mime.startswith('audio'):
        file_type = 'audio'
        folder = 'audio'
    else:
        file_type = 'file'
        folder = 'files'

    upload_path = os.path.join(UPLOAD_DIR, folder)
    os.makedirs(upload_path, exist_ok=True)
    filename = f'{uuid.uuid4()}_{file.filename}'
    filepath = os.path.join(upload_path, filename)

    content = await file.read()
    with open(filepath, 'wb') as f:
        f.write(content)

    attachment = Attachment(
        message_id=message.id,
        room_id=message.room_id,
        file_type=file_type,
        file_url=f'/media/{folder}/{filename}',
        file_name=file.filename,
        mime_type=mime,
        file_size=len(content)
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment


@router.get('/{message_id}', response_model=list[AttachmentOut])
async def get_attachments(
    message_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Attachment).where(Attachment.message_id == message_id)
    )
    return result.scalars().all()