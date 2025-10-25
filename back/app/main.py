from fastapi import FastAPI

from routes import router as transactions_router

# 1. Créer une instance de FastAPI
app = FastAPI()

# Inclure les routes de transactions
app.include_router(transactions_router)

# Inclure les routes de positions


# 2. Définir un "endpoint" (une route)
@app.get("/")
def read_root():
    # 3. Retourner la réponse (FastAPI la convertira en JSON)
    return {"message": "Bonjour le monde !"}

