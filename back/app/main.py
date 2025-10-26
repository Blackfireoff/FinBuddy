from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import os

from routes import router as main_router

# 1. Créer une instance de FastAPI
app = FastAPI()


# Inclure les routes de transactions
app.include_router(main_router)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    os.getenv("CORS_ORIGIN", "http://localhost:3000")
]



app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # ou ["*"] en dev
    allow_credentials=True,
    allow_methods=["*"],  # inclut OPTIONS automatiquement
    allow_headers=["*"],
)
# Inclure les routes de transactions et positions
app.include_router(main_router)


# 2. Définir un "endpoint" (une route)
@app.get("/")
def read_root():
    # 3. Retourner la réponse (FastAPI la convertira en JSON)
    return {"message": "Bonjour le monde !"}
