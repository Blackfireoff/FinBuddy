from fastapi import FastAPI
from routes_transactions import router as transactions_router

# 1. Créer une instance de FastAPI
app = FastAPI()

# Inclure les routes de transactions
app.include_router(transactions_router)

# 2. Définir un "endpoint" (une route)
@app.get("/")
def read_root():
    # 3. Retourner la réponse (FastAPI la convertira en JSON)
    return {"message": "Bonjour le monde !"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


