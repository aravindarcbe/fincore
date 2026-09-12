from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import engine
from .routers import loans, salary, pf, insurance, creditcards, files, dashboard, extract

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FinCore API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(loans.router)
app.include_router(salary.router)
app.include_router(pf.router)
app.include_router(insurance.router)
app.include_router(creditcards.router)
app.include_router(files.router)
app.include_router(dashboard.router)
app.include_router(extract.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
