# -*- coding: utf-8 -*-
"""
FastAPI Backend cho Apartment Chatbot
Để tích hợp với ReactJS frontend
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
from gemini_bot import GeminiChatbot
import uuid

# Khởi tạo FastAPI app
app = FastAPI(
    title="Apartment Chatbot API",
    description="Backend API cho chatbot quản lý chung cư",
    version="1.0.0"
)

# CORS - Cho phép ReactJS gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên chỉ định cụ thể domain của React app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lưu trữ chat sessions cho nhiều users
# Key: session_id, Value: GeminiChatbot instance
chat_sessions: Dict[str, GeminiChatbot] = {}

# ==================== REQUEST/RESPONSE MODELS ====================

class ChatRequest(BaseModel):
    """Request body cho chat endpoint"""
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Response body cho chat endpoint"""
    success: bool
    response: str
    session_id: str
    function_calls: list = []
    error: Optional[str] = None

class SessionResponse(BaseModel):
    """Response cho session creation"""
    session_id: str
    message: str

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "message": "Apartment Chatbot API is running!",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat": "Gửi tin nhắn đến chatbot",
            "POST /session/new": "Tạo session mới",
            "DELETE /session/{session_id}": "Xóa session",
            "GET /sessions": "Xem tất cả sessions"
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint chính để chat với bot

    Body:
    {
        "message": "Có những tiện ích gì?",
        "session_id": "optional-uuid"  // Nếu không có sẽ tạo mới
    }
    """
    try:
        # Lấy hoặc tạo session
        session_id = request.session_id
        if not session_id or session_id not in chat_sessions:
            session_id = str(uuid.uuid4())
            chat_sessions[session_id] = GeminiChatbot()

        # Lấy chatbot instance cho session này
        chatbot = chat_sessions[session_id]

        # Gọi chatbot
        result = chatbot.chat(request.message)

        if result["success"]:
            return ChatResponse(
                success=True,
                response=result["response"],
                session_id=session_id,
                function_calls=result.get("function_calls", [])
            )
        else:
            return ChatResponse(
                success=False,
                response="Xin lỗi, có lỗi xảy ra. Vui lòng thử lại.",
                session_id=session_id,
                error=result.get("error", "Unknown error")
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/session/new", response_model=SessionResponse)
async def create_session():
    """Tạo session mới cho user"""
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = GeminiChatbot()

    return SessionResponse(
        session_id=session_id,
        message="Session created successfully"
    )

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Xóa session (khi user đóng chat)"""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return {"message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.post("/session/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset conversation trong session (giữ nguyên session_id)"""
    if session_id in chat_sessions:
        chat_sessions[session_id].start_new_conversation()
        return {"message": f"Session {session_id} reset successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/sessions")
async def get_sessions():
    """Xem tất cả sessions đang active (cho debug)"""
    return {
        "total_sessions": len(chat_sessions),
        "session_ids": list(chat_sessions.keys())
    }

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check cho monitoring"""
    return {
        "status": "healthy",
        "active_sessions": len(chat_sessions)
    }

# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 80)
    print("🚀 Starting Apartment Chatbot API Server")
    print("=" * 80)
    print("\n📍 Server will run at: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("📊 Alternative docs: http://localhost:8000/redoc")
    print("\n💡 Để test từ ReactJS, gọi POST http://localhost:8000/chat")
    print("\n" + "=" * 80 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)
