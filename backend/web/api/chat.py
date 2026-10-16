from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session

from bi_analysis.database.session import get_db_session
from bi_analysis.database.models import ChatSession, ChatMessage
from bi_analysis.rag.pipeline import create_rag_pipeline
from bi_analysis.config.settings import get_settings

router = APIRouter()
settings = get_settings()


class ChatMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    use_rag: bool = True
    filters: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    temperature: float = 0.7
    stream: bool = False


class ChatMessageResponse(BaseModel):
    role: str
    content: str
    session_id: str
    message_id: int
    sources: Optional[List[Dict[str, Any]]] = None


class ChatSessionResponse(BaseModel):
    session_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime


class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse]


def get_db():
    db = get_db_session()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=ChatMessageResponse)
async def chat(request: ChatMessageRequest, db: Session = Depends(get_db)):
    session_id = request.session_id or str(uuid.uuid4())
    
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        session = ChatSession(
            session_id=session_id,
            title=request.message[:50] if len(request.message) > 50 else request.message,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    db.commit()
    
    if request.use_rag:
        rag = create_rag_pipeline(model=request.model, temperature=request.temperature)
        if request.stream:
            return StreamingResponse(
                stream_chat_response(rag, request.message, request.filters, session.id, db),
                media_type="text/event-stream",
            )
        
        response = rag.query(request.message, where=request.filters)
        
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response.answer,
            extra_data={"sources": [{"content": s.content, "metadata": s.metadata, "distance": s.distance} for s in response.sources]},
            tokens_used=response.tokens_used,
            model=response.model,
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        return ChatMessageResponse(
            role="assistant",
            content=response.answer,
            session_id=session_id,
            message_id=assistant_message.id,
            sources=[{"content": s.content, "metadata": s.metadata, "distance": s.distance} for s in response.sources],
        )
    else:
        from bi_analysis.llm.client import get_ollama_client
        llm = get_ollama_client()
        
        messages = [
            {"role": "system", "content": "Você é um assistente de Business Intelligence especializado em análise de dados. Responda em português do Brasil."},
            {"role": "user", "content": request.message},
        ]
        
        if request.stream:
            return StreamingResponse(
                stream_simple_chat(llm, messages, request.model or settings.ollama_model, request.temperature, session.id, db),
                media_type="text/event-stream",
            )
        
        response = llm.chat(messages=messages, model=request.model, temperature=request.temperature)
        
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response["message"]["content"],
            tokens_used=response.get("eval_count"),
            model=request.model or settings.ollama_model,
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        return ChatMessageResponse(
            role="assistant",
            content=response["message"]["content"],
            session_id=session_id,
            message_id=assistant_message.id,
        )


async def stream_chat_response(rag, message: str, filters: Dict, session_id: int, db: Session):
    documents = rag.retrieve(message, where=filters)
    for chunk in rag.generate_stream(message, documents):
        yield f"data: {json.dumps({'content': chunk})}\n\n"
    
    yield f"data: {json.dumps({'done': True})}\n\n"


async def stream_simple_chat(llm, messages: List[Dict], model: str, temperature: float, session_id: int, db: Session):
    for chunk in llm.chat_stream(messages=messages, model=model, temperature=temperature):
        if "message" in chunk and "content" in chunk["message"]:
            yield f"data: {json.dumps({'content': chunk['message']['content']})}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).limit(50).all()
    return [
        ChatSessionResponse(
            session_id=s.session_id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=ChatHistoryResponse)
async def get_session_history(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at).all()
    
    return ChatHistoryResponse(
        messages=[
            ChatMessageResponse(
                role=m.role,
                content=m.content,
                session_id=session_id,
                message_id=m.id,
                sources=m.extra_data.get("sources") if m.extra_data else None,
            )
            for m in messages
        ]
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(session)
    db.commit()
    return {"message": "Session deleted"}
