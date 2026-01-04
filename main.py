from contextlib import asynccontextmanager
import uuid
from fastapi import Depends, FastAPI, Request 
from fastapi.middleware.cors import CORSMiddleware
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from src.schema import UserCreate, UserRead, UserUpdate
from src.utils.database import Base , get_user_db , create_db_and_tables
from src.routers import router 
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import CookieTransport, JWTStrategy
from src.utils.database import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()
    yield
    
app = FastAPI(title="Invoice Apis", version="v1" , lifespan=lifespan)



# AUthentication set up 
cookie_transport = CookieTransport(cookie_max_age=3600)
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret="SECRET", lifetime_seconds=3600)

from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy

SECRET = "SECRET"

bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Request | None = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Request | None = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Request | None = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

fastapi_users = FastAPIUsers[User, int](
    get_user_manager,  
    [auth_backend],  
)


ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_credentials=True,
    allow_origins=ALLOWED_ORIGINS,
    expose_headers=["*"],
    max_age=600,
)

# Include health endpoints at root level for easier access
@app.get('/ping')
async def health() : 
    return {
        "message" : "Server healthy"
    }

app.include_router(router , prefix='/invoice')
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead , UserUpdate), 
    prefix="/users",
    tags=["users"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
