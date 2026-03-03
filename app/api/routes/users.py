from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db

router = APIRouter(prefix="/users", tags=["users"])

# TODO: GET /users/{id}
# TODO: POST /users          — register
# TODO: PATCH /users/{id}    — update profile
# TODO: DELETE /users/{id}
# TODO: GET /users/{id}/cubes
