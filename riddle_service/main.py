from fastapi import FastAPI, HTTPException
import httpx
from typing import Dict, List, Optional
from pydantic import BaseModel
import random

app = FastAPI()

STORAGE_SERVICE = "http://storage-service:8001"

# База загадок
RIDDLES = {
    "1": {
        "question": "Цвет неба",
        "answer": "голубое",
        "reward": "ключ",
        "health_penalty": 50
    },
    "2": {
        "question": "Какой огонь",
        "answer": "горячий",
        "reward": "руна",
        "health_penalty": 30
    }
}

class RiddleAnswer(BaseModel):
    riddle_id: str
    answer: str

class RiddleResult(BaseModel):
    correct: bool
    message: str
    reward: Optional[str] = None
    health_change: int = 0

@app.get("/riddles")
async def get_riddles():
    return [{"id": k, "question": v["question"]} for k, v in RIDDLES.items()]

@app.get("/riddle/{riddle_id}")
async def get_riddle(riddle_id: str):
    if riddle_id not in RIDDLES:
        raise HTTPException(status_code=404, detail="Riddle not found")
    riddle = RIDDLES[riddle_id]
    return {"id": riddle_id, "question": riddle["question"]}

@app.post("/riddle/{player_id}/check")
async def check_answer(player_id: str, answer_data: RiddleAnswer):
    if answer_data.riddle_id not in RIDDLES:
        raise HTTPException(status_code=404, detail="Riddle not found")
    
    riddle = RIDDLES[answer_data.riddle_id]
    result = RiddleResult(correct=False, message="")
    
    async with httpx.AsyncClient() as client:
        # Получаем данные игрока
        response = await client.get(f"{STORAGE_SERVICE}/player/{player_id}")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player_data = response.json()
        
        # Проверяем ответ
        if answer_data.answer.lower() == riddle["answer"].lower():
            result.correct = True
            result.message = "Правильный ответ!"
            result.reward = riddle["reward"]
            player_data["inventory"].append(riddle["reward"])
        else:
            result.correct = False
            result.message = "Неправильный ответ!"
            result.health_change = -riddle["health_penalty"]
            player_data["health"] -= riddle["health_penalty"]
        
        # Проверяем здоровье игрока
        if player_data["health"] <= 0:
            await client.delete(f"{STORAGE_SERVICE}/player/{player_id}")
            result.message += " Вы погибли!"
            return result
        
        # Обновляем данные игрока
        await client.put(f"{STORAGE_SERVICE}/player/{player_id}", json=player_data)
        return result

@app.get("/riddle/random")
async def get_random_riddle():
    riddle_id = random.choice(list(RIDDLES.keys()))
    riddle = RIDDLES[riddle_id]
    return {"id": riddle_id, "question": riddle["question"]}
