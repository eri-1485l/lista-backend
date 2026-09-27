#Book List — Backend

REST API built with FastAPI to manage a personal list of novels. Protected endpoints validate JWT tokens issued by Keycloak (OAuth2/OIDC).

## Features

- REST API with FastAPI (Python 3.11+)
- JWT authentication (`Authorization: Bearer <token>`)
- Token validation against Keycloak public keys (JWKS endpoint)
- CORS enabled for the Vue frontend at `http://localhost:5173`
- In-memory storage (no persistent database)
- Public health endpoint (`GET /health`)

## Architecture and JWT validation

This backend is part of a three-repository setup: an OpenLDAP + Keycloak lab, a Vue frontend, and this API.

Keycloak federates users from OpenLDAP, but **this service does not query LDAP**. Its only identity job is to check that the JWT in the `Authorization` header is valid.

The flow is:

1. The client (frontend or `curl`) obtains an access token from Keycloak’s `cybersecurity` realm.
2. The client calls the API with `Authorization: Bearer <token>`.
3. The API fetches the realm’s public keys from Keycloak’s JWKS endpoint.
4. With those keys it verifies the signature (RS256), the issuer (`iss`), and the audience (`aud`, matching client id `fastapi-api`).
5. If validation succeeds, the request is handled; otherwise the API returns `401 Unauthorized`.

Keycloak is expected at `http://localhost:8081/realms/cybersecurity`.

## Requirements

- Python 3.11 or later
- Keycloak running (LDAP + Keycloak lab), realm `cybersecurity`, client `fastapi-api`
- (Optional) Vue frontend at `http://localhost:5173`

This API uses port **8001** so it does not conflict with the lab’s demo API, which typically uses port 8000.

## Installation

```bash
python -m venv venv
```

Activate the virtual environment:

```bash
# Linux / macOS
source venv/bin/activate

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Main dependencies: `fastapi`, `uvicorn[standard]`, `python-jose[cryptography]`, `httpx`.

## How to run the server

With the virtual environment activated and Keycloak available:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

The API is served at `http://localhost:8001`. Interactive FastAPI docs are at `http://localhost:8001/docs`.

## Endpoints

| Method | Path         | Description                              | JWT required |
|--------|--------------|------------------------------------------|--------------|
| GET    | `/health`    | Service health check. Response: `{ "status": "ok" }` | No |
| GET    | `/api/books` | Returns the list of books                | Yes          |
| POST   | `/api/books` | Adds a book. Body: `{ "name": string, "description": string }` | Yes |

## Get a JWT (Resource Owner Password Grant)

Replace `USERNAME` and `PASSWORD` with credentials for a user in the realm (typically an LDAP user federated in Keycloak). If the `fastapi-api` client is confidential, also send `client_secret`.

```bash
curl -X POST "http://localhost:8081/realms/cybersecurity/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=fastapi-api" \
  -d "username=USERNAME" \
  -d "password=PASSWORD"
```

Typical response:

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300,
  "refresh_expires_in": 1800,
  "refresh_token": "...",
  "token_type": "Bearer",
  "not-before-policy": 0,
  "session_state": "...",
  "scope": "profile email"
}
```

Copy the `access_token` value for protected requests.

## Call a protected endpoint

List books:

```bash
curl -X GET "http://localhost:8001/api/books" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
```

Add a book:

```bash
curl -X POST "http://localhost:8001/api/books" \
  -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"Mo Dao Zu Shi\", \"description\": \"Cultivation and mystery\"}"
```

Health check (no token):

```bash
curl -X GET "http://localhost:8001/health"
```

## Project structure

```text
lista-backend/
├── app/
│   └── main.py          # FastAPI app, CORS, JWT validation, and endpoints
├── requirements.txt     # Python dependencies
└── README.md
```

## Related repositories

This backend is used together with:

| Repository | Description |
|------------|-------------|
| [lista-frontend](https://github.com/USER/lista-frontend) | Vue frontend (port 5173) |
| [ldap-keycloak-oauth2-lab](https://github.com/USER/ldap-keycloak-oauth2-lab) | Base OpenLDAP + Keycloak lab |

Replace `USER` with the real GitHub organization or account.

## Notes

This project is a **class assignment**. The book list is stored in memory: it is lost when the server restarts, and there is no persistence or built-in user store (only Keycloak token validation). It is not intended for production.
