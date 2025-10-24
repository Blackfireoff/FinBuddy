from fastapi import APIRouter, Query
import requests, os, json
from dotenv import load_dotenv

# Création du routeur FastAPI
router = APIRouter()

# Charger le fichier .env (placé dans le dossier back)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

@router.get("/ai/chat")
async def ai_chat(message: str = Query(..., description="Message utilisateur à envoyer à asi1.ai")):
    """
    Envoie un message à l'API asi1.ai et renvoie la réponse du modèle.
    Exemple: GET /ai/chat?message=Bonjour
    """
    url = "https://api.asi1.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('ASI_ONE_API_KEY')}",
        "Content-Type": "application/json"
    }
    body = {
        "model": "asi1-mini",
        "messages": [{"role": "user", "content": message}]
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        if response.status_code != 200:
            return {"error": "Échec de la requête vers l'API asi1.ai", "status_code": response.status_code}

        data = response.json()
        ai_response = data["choices"][0]["message"]["content"]
        return {"message_sent": message, "response": ai_response}

    except Exception as e:
        return {"error": str(e)}


