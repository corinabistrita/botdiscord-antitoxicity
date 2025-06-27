import json
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
import asyncio
from datetime import datetime
import os

from ai_detector import analyze_message, toxicity_detector
from database import db_manager

   
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Discord Moderation Bot API",
    description="API pentru sistemul de moderare Discord cu AI",
    version="1.0.0"
)

   
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

   
if os.path.exists("dashboard"):
    app.mount("/static", StaticFiles(directory="dashboard"), name="static")

   
class TextAnalysisRequest(BaseModel):
    text: str
    guild_id: Optional[str] = None

class TextAnalysisResponse(BaseModel):
    text: str
    is_toxic: bool
    category: str
    action: str
    confidence: float
    scores: Dict[str, float]

class ServerConfigRequest(BaseModel):
    guild_id: str
    toxicity_threshold: Optional[float] = None
    auto_moderation: Optional[bool] = None
    log_channel_id: Optional[str] = None
    admin_role_id: Optional[str] = None
    language: Optional[str] = None
    strict_mode: Optional[bool] = None

class DashboardStatsResponse(BaseModel):
    total_messages: int
    toxic_messages: int
    warnings: int
    mutes: int
    bans: int
    risky_users: List[Dict]
    daily_activity: List[Dict]

class UserWarning(BaseModel):
    user_id: str
    username: str
    warnings: int
    mutes: int
    bans: int
    risk_level: str

   
@app.on_event("startup")
async def startup_event():
    """Inițializează baza de date și modelul AI la startup"""
    logger.info("Inițializare API...")
    await db_manager.init_database()
    await toxicity_detector.load_model()
    logger.info("API gata!")

   
@app.get("/")
async def serve_dashboard():
    """Servește dashboard-ul principal"""
    dashboard_path = "dashboard/index.html"
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    else:
        return {"message": "Dashboard-ul va fi disponibil curând!", "api_version": "1.0.0"}

   
@app.get("/api/health")
async def health_check():
    """Verifică starea API-ului"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_model_loaded": toxicity_detector.model is not None
    }

   
@app.post("/api/analyze", response_model=TextAnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """Analizează un text pentru toxicitate"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Textul nu poate fi gol")
        
        analysis = await analyze_message(request.text)
        
        return TextAnalysisResponse(
            text=request.text,
            is_toxic=analysis['is_toxic'],
            category=analysis['category'],
            action=analysis['action'],
            confidence=analysis['confidence'],
            scores=analysis['scores']
        )
    
    except Exception as e:
        logger.error(f"Eroare la analiză: {e}")
        raise HTTPException(status_code=500, detail=f"Eroare la analizarea textului: {str(e)}")

   
@app.get("/api/stats/{guild_id}", response_model=DashboardStatsResponse)
async def get_dashboard_stats(guild_id: str, days: int = 7):
    """Obține statistici pentru dashboard"""
    try:
        if days < 1 or days > 365:
            raise HTTPException(status_code=400, detail="Numărul de zile trebuie să fie între 1 și 365")
        
        stats = await db_manager.get_dashboard_stats(guild_id, days)
        
        return DashboardStatsResponse(**stats)
    
    except Exception as e:
        logger.error(f"Eroare la obținerea statisticilor: {e}")
        raise HTTPException(status_code=500, detail=f"Eroare la obținerea statisticilor: {str(e)}")

   
@app.get("/api/config/{guild_id}")
async def get_server_config(guild_id: str):
    """Obține configurația serverului"""
    try:
        config = await db_manager.get_server_config(guild_id)
        return config
    except Exception as e:
        logger.error(f"Eroare la obținerea configurației: {e}")
        raise HTTPException(status_code=500, detail=f"Eroare la obținerea configurației: {str(e)}")

@app.post("/api/config")
async def update_server_config(request: ServerConfigRequest):
    """Actualizează configurația serverului"""
    try:
           
        config = await db_manager.get_server_config(request.guild_id)
        
           
        if request.toxicity_threshold is not None:
            if not 0.0 <= request.toxicity_threshold <= 1.0:
                raise HTTPException(status_code=400, detail="Pragul trebuie să fie între 0.0 și 1.0")
            config['toxicity_threshold'] = request.toxicity_threshold
        
        if request.auto_moderation is not None:
            config['auto_moderation'] = request.auto_moderation
        
        if request.log_channel_id is not None:
            config['log_channel_id'] = request.log_channel_id
        
        if request.admin_role_id is not None:
            config['admin_role_id'] = request.admin_role_id
        
        if request.language is not None:
            if request.language not in ['ro', 'en', 'es', 'fr', 'de']:
                raise HTTPException(status_code=400, detail="Limbă nesuportată")
            config['language'] = request.language
        
        if request.strict_mode is not None:
            config['strict_mode'] = request.strict_mode
        
           
        await db_manager.save_server_config(config)
        
        return {"message": "Configurația a fost actualizată cu succes", "config": config}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Eroare la actualizarea configurației: {e}")
        raise HTTPException(status_code=500, detail=f"Eroare la actualizarea configurației: {str(e)}")

   
@app.get("/api/messages/{guild_id}")
async def get_moderated_messages(guild_id: str, limit: int = 50, offset: int = 0):
    """Obține mesajele moderate recent"""
    try:
        if limit > 100:
            limit = 100
        
        async with await db_manager.get_connection() as db:
            cursor = await db.execute("""
                SELECT user_id, username, channel_id, message_content, 
                       toxicity_scores, is_toxic, category, action_taken, 
                       confidence, timestamp
                FROM moderated_messages 
                WHERE guild_id = ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
            """, (guild_id, limit, offset))
            
            messages = await cursor.fetchall()
            
            result = []
            for msg in messages:
                result.append({
                    'user_id': msg[0],
                    'username': msg[1],
                    'channel_id': msg[2],
                    'message_content': msg[3],
                    'toxicity_scores': json.loads(msg[4]) if msg[4] else {},
                    'is_toxic': bool(msg[5]),
                    'category': msg[6],
                    'action_taken': msg[7],
                    'confidence': msg[8],
                    'timestamp': msg[9]
                })
            
            return {
                'messages': result,
                'total': len(result),
                'offset': offset,
                'limit': limit
            }
    
    except Exception as e:
        logger.error(f"Eroare la obținerea mesajelor: {e}")
        raise HTTPException(status_code=500, detail=f"Eroare la obținerea mesajelor: {str(e)}")

   
@app.get("/api/risky-users/{guild_id}")
async def get_risky_users(guild_id: str, limit: int = 20):
    """Obține utilizatorii cu risc ridicat"""
    try:
        async with await db_manager.get_connection() as db:
            cursor = await db.execute("""
                SELECT user_id, username, warning_count, mute_count, ban_count, 
                       risk_level, last_violation
                FROM user_warnings 
                WHERE guild_id = ?
                ORDER BY (warning_count + mute_count * 2 + ban_count * 5) DESC
                LIMIT ?
            """, (guild_id, limit))
            
            users = await cursor.fetchall()
            
            result = []
            for user in users:
                result.append({
                    'user_id': user[0],
                    'username': user[1],
                    'warning_count': user[2],
                    'mute_count': user[3],
                    'ban_count': user[4],
                    'risk_level': user[5],
                    'last_violation': user[6],
                    'total_violations': user[2] + user[3] * 2 + user[4] * 5
                })
            
            return {'users': result}
    
    except Exception as e:
        logger.error(f"Eroare la obținerea utilizatorilor cu risc: {e}")
        raise HTTPException(status_code=500, detail=f"Eroare la obținerea utilizatorilor cu risc: {str(e)}")

   
@app.get("/api/daily-activity/{guild_id}")
async def get_daily_activity(guild_id: str, days: int = 30):
    """Obține activitatea zilnică"""
    try:
        if days > 90:
            days = 90
        
        async with await db_manager.get_connection() as db:
            cursor = await db.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as total_messages,
                    SUM(CASE WHEN is_toxic = 1 THEN 1 ELSE 0 END) as toxic_messages,
                    SUM(CASE WHEN action_taken = 'warning' THEN 1 ELSE 0 END) as warnings,
                    SUM(CASE WHEN action_taken = 'mute' THEN 1 ELSE 0 END) as mutes,
                    SUM(CASE WHEN action_taken = 'ban' THEN 1 ELSE 0 END) as bans
                FROM moderated_messages 
                WHERE guild_id = ? AND timestamp >= datetime('now', '-{} days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """.format(days), (guild_id,))
            
            activity = await cursor.fetchall()
            
            result = []
            for day in activity:
                result.append({
                    'date': day[0],
                    'total_messages': day[1],
                    'toxic_messages': day[2],
                    'warnings': day[3],
                    'mutes': day[4],
                    'bans': day[5]
                })
            
            return {'activity': result}
    
    except Exception as e:
        logger.error(f"Eroare la obținerea activității zilnice: {e}")
        raise HTTPException(status_code=500, detail=f"Eroare la obținerea activității zilnice: {str(e)}")

   
@app.post("/api/feedback")
async def submit_feedback(feedback_data: dict):
    """Primește feedback despre moderare"""
    try:
           
           
        logger.info(f"Feedback primit: {feedback_data}")
        
        return {"message": "Feedback înregistrat cu succes", "status": "success"}
    
    except Exception as e:
        logger.error(f"Eroare la înregistrarea feedback-ului: {e}")
        raise HTTPException(status_code=500, detail=f"Eroare la înregistrarea feedback-ului: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)