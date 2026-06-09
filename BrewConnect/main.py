import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from passlib.context import CryptContext
from jose import JWTError, jwt
from contextlib import asynccontextmanager
from typing import Dict, List
import json

from database import get_db, init_db
from models import User, Interest, ActiveSession, Message
from schemas import UserCreate, UserLogin, TokenOut, UserOut, SessionToggle, ProfileUpdate, MessageCreate, MessageOut, ConversationOut
from ml_matching import rank_nearby_users, bounding_box
from config import (SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
                    MAX_RADIUS_KM, DISTANCE_WEIGHT, INTEREST_WEIGHT,
                    ACTIVE_SESSION_TIMEOUT_MIN)

os.makedirs("static", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = next(get_db())
    for tag in INTEREST_TAGS:
        if not db.query(Interest).filter_by(name=tag).first():
            db.add(Interest(name=tag))
    db.commit(); db.close()
    print("[OK] BrewConnect API ready — http://localhost:8000")
    yield

app = FastAPI(title="BrewConnect API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
auth_scheme = HTTPBearer()

INTEREST_TAGS = [
    "Machine Learning","Startups","Jazz","Photography","Travel","Coffee","Books",
    "Gaming","Fitness","Design","Finance","Coding","Music","Art","Writing",
    "Philosophy","Science","Food","Movies","Yoga","Entrepreneurship","Marketing"
]

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(json.dumps(message, default=str))
                except Exception:
                    pass

manager = ConnectionManager()
def make_token(uid: int) -> str:
    return jwt.encode({"sub": str(uid), "exp": datetime.utcnow() +
                       timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
                      SECRET_KEY, algorithm=ALGORITHM)


def current_user(creds: HTTPAuthorizationCredentials = Depends(auth_scheme),
                 db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        uid = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(401, "Invalid or expired token")
    u = db.query(User).filter_by(id=uid).first()
    if not u: raise HTTPException(401, "User not found")
    return u


def user_dict(user: User, session: ActiveSession = None) -> dict:
    return {
        "user_id": user.id, "username": user.username,
        "display_name": user.display_name, "bio": user.bio or "",
        "avatar_url": user.avatar_url or "",
        "interests": [i.name for i in user.interests],
        "latitude":  session.latitude   if session else 0.0,
        "longitude": session.longitude  if session else 0.0,
        "venue_name": session.venue_name if session else "",
        "mood_tag":   session.mood_tag   if session else "",
        "last_seen":  session.last_seen  if session else datetime.utcnow(),
    }


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/")
def root(): return FileResponse("static/index.html")

@app.get("/api/interests")
def interests(db: Session = Depends(get_db)):
    return [{"id": i.id, "name": i.name} for i in db.query(Interest).order_by(Interest.name)]

@app.post("/api/auth/register", response_model=TokenOut, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter_by(username=body.username).first():
        raise HTTPException(400, "Username already taken")
    if db.query(User).filter_by(email=body.email).first():
        raise HTTPException(400, "Email already registered")
    user = User(username=body.username, email=body.email,
                hashed_password=pwd.hash(body.password),
                display_name=body.display_name, bio=body.bio or "")
    for name in (body.interests or []):
        interest = db.query(Interest).filter_by(name=name).first() or Interest(name=name)
        if interest not in user.interests: user.interests.append(interest)
    db.add(user); db.commit(); db.refresh(user)
    return {"access_token": make_token(user.id), "token_type": "bearer", "user": user}

@app.post("/api/auth/login", response_model=TokenOut)
def login(body: UserLogin, db: Session = Depends(get_db)):
    u = db.query(User).filter_by(username=body.username).first()
    if not u or not pwd.verify(body.password, u.hashed_password):
        raise HTTPException(401, "Incorrect username or password")
    return {"access_token": make_token(u.id), "token_type": "bearer", "user": u}

@app.get("/api/auth/me", response_model=UserOut)
def me(u: User = Depends(current_user)): return u

@app.put("/api/profile", response_model=UserOut)
def update_profile(body: ProfileUpdate, u: User = Depends(current_user),
                   db: Session = Depends(get_db)):
    if body.display_name is not None: u.display_name = body.display_name
    if body.bio          is not None: u.bio          = body.bio
    if body.interests    is not None:
        u.interests.clear()
        for name in body.interests:
            interest = db.query(Interest).filter_by(name=name).first() or Interest(name=name)
            if interest not in u.interests: u.interests.append(interest)
    db.commit(); db.refresh(u); return u

@app.post("/api/session/toggle")
def toggle(body: SessionToggle, u: User = Depends(current_user),
           db: Session = Depends(get_db)):
    s = db.query(ActiveSession).filter_by(user_id=u.id).first()
    if s:
        s.latitude=body.latitude; s.longitude=body.longitude
        s.is_active=body.is_active; s.venue_name=body.venue_name or ""
        s.mood_tag=body.mood_tag or ""; s.last_seen=datetime.utcnow()
        if body.is_active: s.activated_at = datetime.utcnow()
    else:
        s = ActiveSession(user_id=u.id, latitude=body.latitude,
                          longitude=body.longitude, is_active=body.is_active,
                          venue_name=body.venue_name or "", mood_tag=body.mood_tag or "")
        db.add(s)
    db.commit(); db.refresh(s)
    return {"status": "active" if s.is_active else "inactive",
            "latitude": s.latitude, "longitude": s.longitude,
            "venue_name": s.venue_name, "mood_tag": s.mood_tag}

@app.get("/api/session/status")
def session_status(u: User = Depends(current_user), db: Session = Depends(get_db)):
    s = db.query(ActiveSession).filter_by(user_id=u.id).first()
    if not s: return {"is_active": False}
    return {"is_active": s.is_active, "latitude": s.latitude, "longitude": s.longitude,
            "venue_name": s.venue_name, "mood_tag": s.mood_tag, "last_seen": s.last_seen}

@app.get("/api/discover")
def discover(lat: float, lon: float, radius_km: float = MAX_RADIUS_KM,
             u: User = Depends(current_user), db: Session = Depends(get_db)):
    # Expire stale sessions
    cutoff = datetime.utcnow() - timedelta(minutes=ACTIVE_SESSION_TIMEOUT_MIN)
    db.query(ActiveSession).filter(ActiveSession.last_seen < cutoff,
                                   ActiveSession.is_active == True).update({"is_active": False})
    db.commit()
    lat_min,lat_max,lon_min,lon_max = bounding_box(lat, lon, radius_km)
    rows = db.query(ActiveSession, User).join(User).filter(
        ActiveSession.is_active  == True,
        ActiveSession.user_id    != u.id,
        ActiveSession.latitude.between(lat_min, lat_max),
        ActiveSession.longitude.between(lon_min, lon_max),
    ).all()
    candidates = [user_dict(usr, ses) for ses, usr in rows]
    if not candidates: return {"results": [], "count": 0}
    ranked = rank_nearby_users(
        {"bio": u.bio or "", "interests": [i.name for i in u.interests]},
        candidates, lat, lon, radius_km, DISTANCE_WEIGHT, INTEREST_WEIGHT)
    return {"results": ranked, "count": len(ranked)}


def get_user_from_token_query(token: str, db: Session):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uid = int(payload.get("sub"))
        user = db.query(User).filter_by(id=uid).first()
        if user is None:
            raise Exception("User not found")
        return user
    except Exception:
        raise Exception("Invalid token")

@app.websocket("/api/ws/messages")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...), db: Session = Depends(get_db)):
    try:
        user = get_user_from_token_query(token, db)
    except Exception:
        await websocket.close(code=1008)
        return
        
    await manager.connect(user.id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                rec_id = payload.get("recipient_id")
                content = payload.get("content")
                if rec_id and content:
                    msg = Message(sender_id=user.id, recipient_id=rec_id, content=content)
                    db.add(msg)
                    db.commit()
                    db.refresh(msg)
                    
                    out_msg = MessageOut.model_validate(msg).model_dump()
                    out_msg['created_at'] = out_msg['created_at'].isoformat()
                    
                    await manager.send_personal_message(out_msg, user.id)
                    await manager.send_personal_message(out_msg, rec_id)
            except Exception as e:
                print("WS Error:", e)
    except WebSocketDisconnect:
        manager.disconnect(user.id, websocket)

@app.get("/api/messages/conversations", response_model=List[ConversationOut])
def get_conversations(u: User = Depends(current_user), db: Session = Depends(get_db)):
    messages = db.query(Message).filter(
        or_(Message.sender_id == u.id, Message.recipient_id == u.id)
    ).order_by(desc(Message.created_at)).all()
    
    convos = {}
    for msg in messages:
        other_id = msg.sender_id if msg.recipient_id == u.id else msg.recipient_id
        if other_id not in convos:
            other_user = db.query(User).filter_by(id=other_id).first()
            if not other_user: continue
            
            unread = sum(1 for m in messages if m.sender_id == other_id and m.recipient_id == u.id and not m.is_read)
            
            convos[other_id] = ConversationOut(
                user=UserOut.model_validate(other_user),
                last_message=MessageOut.model_validate(msg),
                unread_count=unread
            )
    return list(convos.values())

@app.get("/api/messages/{other_id}", response_model=List[MessageOut])
def get_messages(other_id: int, u: User = Depends(current_user), db: Session = Depends(get_db)):
    messages = db.query(Message).filter(
        or_(
            (Message.sender_id == u.id) & (Message.recipient_id == other_id),
            (Message.sender_id == other_id) & (Message.recipient_id == u.id)
        )
    ).order_by(Message.created_at).all()
    
    for msg in messages:
        if msg.recipient_id == u.id and not msg.is_read:
            msg.is_read = True
    db.commit()
    return messages

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)