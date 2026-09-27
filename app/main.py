from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import List
import httpx

app = FastAPI(title="Lista de Libros Danmei - Backend")

# CORS: permitimos que el frontend (Vue en localhost:5173) hable con este backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración del realm de Keycloak
KEYCLOAK_URL = "http://localhost:8081/realms/cybersecurity"
CLIENT_ID = "fastapi-api"

# Esquema de seguridad: exige el header "Authorization: Bearer <token>"
security = HTTPBearer()

# Modelo de datos para un libro
class Book(BaseModel):
    id: int
    name: str
    description: str

class BookCreate(BaseModel):
    name: str
    description: str

# "Base de datos" en memoria con libros danmei
books_db: List[Book] = [
    Book(id=1, name="Mo Dao Zu Shi", description="Género de cultivo y misterio"),
    Book(id=2, name="Tian Guan Ci Fu", description="Género de dioses y fantasmas"),
    Book(id=3, name="Erha and His White Cat Shizun", description="Género de cultivo y romance"),
    Book(id=4, name="Xiao Mogu", description="Género de ciencia ficción"),
    Book(id=5, name="Qiang Jin Jiu", description="Género de intriga política"),
]

# Función que valida el JWT contra las llaves públicas de Keycloak
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        async with httpx.AsyncClient() as client:
            jwks_url = f"{KEYCLOAK_URL}/protocol/openid-connect/certs"
            response = await client.get(jwks_url)
            jwks = response.json()

        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }

        if not rsa_key:
            raise HTTPException(status_code=401, detail="No matching key found")

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=KEYCLOAK_URL,
        )
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ----- Endpoints -----

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/books", response_model=List[Book])
async def get_books(payload: dict = Depends(verify_token)):
    print(f"✅ GET /api/books - Usuario: {payload.get('preferred_username')}")
    return books_db

@app.post("/api/books", response_model=Book)
async def create_book(book: BookCreate, payload: dict = Depends(verify_token)):
    print(f"✅ POST /api/books - Usuario: {payload.get('preferred_username')}")
    new_id = max([b.id for b in books_db], default=0) + 1
    new_book = Book(id=new_id, name=book.name, description=book.description)
    books_db.append(new_book)
    return new_book