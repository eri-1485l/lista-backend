import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi_armor.middleware import ArmorMiddleware
from starlette.middleware.base import BaseHTTPMiddleware  # NUEVO
from jose import jwt, JWTError
from pydantic import BaseModel
from typing import List
import httpx

app = FastAPI(
    title="Lista de Libros - Backend",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(ArmorMiddleware, preset="strict")

# middleware para el header que falta
class ExtraHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        return response

app.add_middleware(ExtraHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de Keycloak (separando interna y pública)
KEYCLOAK_INTERNAL_URL = os.getenv("KEYCLOAK_INTERNAL_URL", "http://keycloak:8080")
KEYCLOAK_PUBLIC_URL = os.getenv("KEYCLOAK_PUBLIC_URL", "http://localhost:8081")
REALM = "cybersecurity"
CLIENT_ID = "fastapi-api"

ISSUER = f"{KEYCLOAK_PUBLIC_URL}/realms/{REALM}"
JWKS_URL = f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/certs"

security = HTTPBearer()

class Book(BaseModel):
    id: int
    name: str
    description: str

class BookCreate(BaseModel):
    name: str
    description: str

books_db: List[Book] = [
    Book(id=1, name="Mo Dao Zu Shi", description="Género de cultivo y misterio"),
    Book(id=2, name="Tian Guan Ci Fu", description="Género de dioses y fantasmas"),
    Book(id=3, name="Erha and His White Cat Shizun", description="Género de cultivo y romance"),
    Book(id=4, name="Xiao Mogu", description="Género de ciencia ficción"),
    Book(id=5, name="Qiang Jin Jiu", description="Género de intriga política"),
]

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(JWKS_URL)
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
            issuer=ISSUER,
        )
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
