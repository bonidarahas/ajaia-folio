"""Ajaia Docs — scoped document collaboration demo.

Authentication is deliberately simulated using X-User-ID. Do not deploy with private data.
"""
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import bleach
import mistune
from fastapi import FastAPI, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

BASE_DIR = Path(__file__).parent
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR / "ajaia.db"}')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql+psycopg://', 1)
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {}, pool_pre_ping=True)
SessionLocal = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True)


class Document(Base):
    __tablename__ = 'documents'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    content: Mapped[str] = mapped_column(Text, default='')
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Share(Base):
    __tablename__ = 'shares'
    __table_args__ = (UniqueConstraint('document_id', 'user_id'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default='editor')


def init_db():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.scalar(select(User.id).limit(1)):
            db.add_all([
                User(id=1, name='Alex Morgan', email='alex@demo.test'),
                User(id=2, name='Jordan Lee', email='jordan@demo.test'),
                User(id=3, name='Sam Rivera', email='sam@demo.test'),
            ])
            db.commit()


init_db()
app = FastAPI(title='Ajaia Docs', version='1.0')

ALLOWED_TAGS = ['p', 'br', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'ul', 'ol', 'li', 'blockquote', 'div', 'span']
ALLOWED_ATTRIBUTES = {}
MAX_HTML = 250_000
MAX_UPLOAD = 512 * 1024


def clean_html(raw: str) -> str:
    return bleach.clean(raw, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


def get_db():
    with SessionLocal() as session:
        yield session


def current_user(x_user_id: Optional[int] = Header(default=None), db: Session = Depends(get_db)) -> User:
    if x_user_id is None:
        raise HTTPException(401, 'Choose a demo user')
    user = db.get(User, x_user_id)
    if user is None:
        raise HTTPException(401, 'Unknown demo user')
    return user


def permitted(doc_id: int, db: Session, user: User, owner_only: bool = False) -> Document:
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(404, 'Document not found')
    if doc.owner_id != user.id:
        if owner_only or db.scalar(select(Share.id).where(Share.document_id == doc_id, Share.user_id == user.id)) is None:
            raise HTTPException(403, 'You do not have access to this document')
    return doc


def doc_json(doc: Document, db: Session, user: User, include_content: bool = True):
    owner = db.get(User, doc.owner_id)
    result = {'id': doc.id, 'title': doc.title, 'owner_id': doc.owner_id,
              'owner_name': owner.name, 'is_owner': doc.owner_id == user.id,
              'updated_at': doc.updated_at.isoformat()}
    if include_content:
        result['content'] = doc.content
        if doc.owner_id == user.id:
            shares = db.scalars(select(Share).where(Share.document_id == doc.id)).all()
            result['shares'] = [{'user_id': s.user_id, 'name': db.get(User, s.user_id).name, 'role': s.role} for s in shares]
        else:
            result['shares'] = []
    return result


class CreateDoc(BaseModel):
    title: str = Field(default='Untitled document', min_length=1, max_length=150)


class UpdateDoc(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=150)
    content: Optional[str] = Field(default=None, max_length=MAX_HTML)


class ShareInput(BaseModel):
    user_id: int


@app.get('/api/health')
def health():
    return {'status': 'ok'}


@app.get('/api/users')
def users(db: Session = Depends(get_db)):
    return [{'id': u.id, 'name': u.name, 'email': u.email} for u in db.scalars(select(User).order_by(User.id))]


@app.get('/api/documents')
def list_documents(user: User = Depends(current_user), db: Session = Depends(get_db)):
    owned = db.scalars(select(Document).where(Document.owner_id == user.id).order_by(Document.updated_at.desc())).all()
    shared_ids = db.scalars(select(Share.document_id).where(Share.user_id == user.id)).all()
    shared = db.scalars(select(Document).where(Document.id.in_(shared_ids)).order_by(Document.updated_at.desc())).all() if shared_ids else []
    return {'owned': [doc_json(d, db, user, False) for d in owned],
            'shared': [doc_json(d, db, user, False) for d in shared]}


@app.post('/api/documents', status_code=201)
def create_document(body: CreateDoc, user: User = Depends(current_user), db: Session = Depends(get_db)):
    title = body.title.strip()
    if not title:
        raise HTTPException(422, 'Title cannot be empty')
    doc = Document(title=title, owner_id=user.id, content='<p></p>')
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc_json(doc, db, user)


@app.get('/api/documents/{doc_id}')
def get_document(doc_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return doc_json(permitted(doc_id, db, user), db, user)


@app.patch('/api/documents/{doc_id}')
def update_document(doc_id: int, body: UpdateDoc, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = permitted(doc_id, db, user)
    if body.title is not None:
        if not body.title.strip():
            raise HTTPException(422, 'Title cannot be empty')
        doc.title = body.title.strip()
    if body.content is not None:
        doc.content = clean_html(body.content)
    doc.updated_at = datetime.now(timezone.utc)
    db.commit()
    return doc_json(doc, db, user)


@app.post('/api/documents/{doc_id}/share', status_code=201)
def share_document(doc_id: int, body: ShareInput, user: User = Depends(current_user), db: Session = Depends(get_db)):
    doc = permitted(doc_id, db, user, owner_only=True)
    target = db.get(User, body.user_id)
    if target is None:
        raise HTTPException(404, 'User not found')
    if target.id == doc.owner_id:
        raise HTTPException(422, 'Owner already has access')
    exists = db.scalar(select(Share).where(Share.document_id == doc_id, Share.user_id == target.id))
    if exists is None:
        db.add(Share(document_id=doc_id, user_id=target.id))
        db.commit()
    return doc_json(doc, db, user)


@app.delete('/api/documents/{doc_id}/share/{target_id}', status_code=204)
def revoke_share(doc_id: int, target_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    permitted(doc_id, db, user, owner_only=True)
    item = db.scalar(select(Share).where(Share.document_id == doc_id, Share.user_id == target_id))
    if item is None:
        raise HTTPException(404, 'Share not found')
    db.delete(item)
    db.commit()


@app.post('/api/import', status_code=201)
async def import_document(file: UploadFile = File(...), user: User = Depends(current_user), db: Session = Depends(get_db)):
    filename = file.filename or ''
    suffix = Path(filename).suffix.lower()
    if suffix not in {'.txt', '.md'}:
        raise HTTPException(415, 'Only .txt and .md files are supported')
    raw = await file.read(MAX_UPLOAD + 1)
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, 'File exceeds 512 KB limit')
    try:
        content = raw.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(422, 'Upload a UTF-8 encoded text file')
    if suffix == '.md':
        html = clean_html(mistune.html(content))
    else:
        import html as html_lib
        lines = content.splitlines()
        html = ''.join(f'<p>{html_lib.escape(line)}</p>' for line in lines) or '<p></p>'
    title = re.sub(r'[^\w\s().\-]', '', Path(filename).stem).strip()[:150] or 'Imported document'
    doc = Document(title=title, content=html, owner_id=user.id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc_json(doc, db, user)


@app.get('/')
def index():
    return FileResponse(BASE_DIR / 'static' / 'index.html')


@app.get('/app.js')
def script():
    return FileResponse(BASE_DIR / 'static' / 'app.js', media_type='application/javascript')


@app.get('/style.css')
def style():
    return FileResponse(BASE_DIR / 'static' / 'style.css', media_type='text/css')
