from fastapi import FastAPI

from app.db.session import engine
from app.db.base import Base
from app.api.routes import cards, users, stats

app = FastAPI(title="AetherGyre")

Base.metadata.create_all(bind=engine)

app.include_router(cards.router)
app.include_router(users.router)
app.include_router(stats.router)