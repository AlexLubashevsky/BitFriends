from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

# Allow CORS for local dev and Telegram
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory user data (replace with file/db in production)
users: Dict[str, dict] = {}

class PetAction(BaseModel):
    user_id: str

class BuySkinRequest(BaseModel):
    user_id: str
    skin: str

class ConfirmPaymentRequest(BaseModel):
    user_id: str
    skin: str
    tx: str
    chain: str  # 'sol' or 'eth'

@app.post("/pet/status")
def get_pet_status(data: PetAction):
    user = users.setdefault(data.user_id, {
        "hunger": 50,
        "happiness": 50,
        "skin": "default",
        "coins": 100,
        "owned_skins": ["default"]
    })
    return user

@app.post("/pet/feed")
def feed_pet(data: PetAction):
    user = users.setdefault(data.user_id, {
        "hunger": 50,
        "happiness": 50,
        "skin": "default",
        "coins": 100,
        "owned_skins": ["default"]
    })
    user["hunger"] = min(100, user["hunger"] + 20)
    return user

@app.post("/pet/play")
def play_pet(data: PetAction):
    user = users.setdefault(data.user_id, {
        "hunger": 50,
        "happiness": 50,
        "skin": "default",
        "coins": 100,
        "owned_skins": ["default"]
    })
    user["happiness"] = min(100, user["happiness"] + 15)
    user["hunger"] = max(0, user["hunger"] - 10)
    return user

@app.post("/pet/set_skin")
def set_skin(data: BuySkinRequest):
    user = users.setdefault(data.user_id, {
        "hunger": 50,
        "happiness": 50,
        "skin": "default",
        "coins": 100,
        "owned_skins": ["default"]
    })
    if data.skin in user["owned_skins"]:
        user["skin"] = data.skin
    return user

@app.post("/shop/buy")
def buy_skin(data: BuySkinRequest):
    user = users.setdefault(data.user_id, {
        "hunger": 50,
        "happiness": 50,
        "skin": "default",
        "coins": 100,
        "owned_skins": ["default"]
    })
    # For demo, just add skin (no payment check)
    if data.skin not in user["owned_skins"]:
        user["owned_skins"].append(data.skin)
    return user

@app.post("/shop/confirm_payment")
def confirm_payment(data: ConfirmPaymentRequest):
    user = users.setdefault(data.user_id, {
        "hunger": 50,
        "happiness": 50,
        "skin": "default",
        "coins": 100,
        "owned_skins": ["default"]
    })
    # For demo, just add skin
    if data.skin not in user["owned_skins"]:
        user["owned_skins"].append(data.skin)
    return user 