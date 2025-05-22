from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from jose import JWTError, jwt
import asyncio

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

fake_users_db = {
    "sindico": {"username": "sindico", "password": "123", "role": "sindico"},
    "portaria": {"username": "portaria", "password": "123", "role": "portaria"}
}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    role: str

class UserInDB(User):
    password: str

class Visit(BaseModel):
    nome: str
    cpf: str
    apartamento: str
    placa: str
    vaga: str
    motivo: str
    data: datetime = datetime.now()

class ConfiguracaoVisual(BaseModel):
    cor_primaria: str
    cor_secundaria: str
    cor_terciaria: str
    logo_url: Optional[str]

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

visitas: List[Visit] = []
visual_config = ConfiguracaoVisual(cor_primaria="#003366", cor_secundaria="#336699", cor_terciaria="#99CCFF")

subscribers = []

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if user and user["password"] == password:
        return UserInDB(**user)
    return None

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")
        user = fake_users_db.get(username)
        return User(**user)
    except JWTError:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Usuário ou senha incorretos")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/visitas")
async def registrar_visita(visita: Visit):
    visitas.append(visita)
    for queue in subscribers:
        await queue.put(visita)
    return {"msg": "Visita registrada com sucesso"}

@app.get("/stream")
async def stream():
    async def event_generator():
        queue = asyncio.Queue()
        subscribers.append(queue)
        try:
            while True:
                visita = await queue.get()
                yield f"data: {visita.json()}

"
        except asyncio.CancelledError:
            subscribers.remove(queue)
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/visitas", response_model=List[Visit])
async def listar_visitas(current_user: User = Depends(get_current_user)):
    return visitas

@app.get("/configuracao", response_model=ConfiguracaoVisual)
async def get_config():
    return visual_config

@app.post("/configuracao")
async def set_config(config: ConfiguracaoVisual, current_user: User = Depends(get_current_user)):
    global visual_config
    visual_config = config
    return {"msg": "Configuração atualizada"}