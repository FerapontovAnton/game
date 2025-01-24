from fastapi import FastAPI, HTTPException
import httpx
from typing import Dict, Optional
from pydantic import BaseModel

app = FastAPI()

STORAGE_SERVICE = "http://storage-service:8001"

# Конфигурация локаций
LOCATIONS = {
    "lake": {
        "name": "Озеро",
        "description": "Таинственное озеро с темной водой",
        "actions": ["forward", "right", "left", "back"]
    }
}

class ActionResult(BaseModel):
    message: str
    success: bool
    health_change: int = 0
    mana_change: int = 0
    items_added: list = []
    items_removed: list = []

@app.get("/location/{location_id}")
async def get_location(location_id: str):
    if location_id not in LOCATIONS:
        raise HTTPException(status_code=404, detail="Location not found")
    return LOCATIONS[location_id]

@app.post("/location/{location_id}/{player_id}/action")
async def perform_action(location_id: str, player_id: str, action: str):
    if location_id not in LOCATIONS:
        raise HTTPException(status_code=404, detail="Location not found")
    
    async with httpx.AsyncClient() as client:
        # Получаем данные игрока
        response = await client.get(f"{STORAGE_SERVICE}/player/{player_id}")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player_data = response.json()
        result = ActionResult(message="", success=True)

        # Логика действий в локации озера
        if location_id == "lake":
            if action == "forward":
                player_data["health"] -= 20
                result.health_change = -20
                result.message = "Вы поплыли прямо и наткнулись на корягу"
                
            elif action == "right":
                player_data["mana"] += 10
                result.mana_change = 10
                if "руна" not in player_data["inventory"]:
                    player_data["inventory"].append("руна")
                    result.items_added.append("руна")
                result.message = "Вы поплыли направо и нашли руну"
                
            elif action == "left":
                if "зелье" in player_data["inventory"]:
                    player_data["health"] += 50
                    result.health_change = 50
                    player_data["inventory"].remove("зелье")
                    result.items_removed.append("зелье")
                    result.message = "Вы использовали зелье и восстановили здоровье"
                else:
                    player_data["health"] -= 10
                    result.health_change = -10
                    result.message = "Вы поплыли налево, но ничего не нашли"
                    
            elif action == "back":
                player_data["inventory"].append("зелье")
                result.items_added.append("зелье")
                result.message = "Вы нашли зелье"
            
            else:
                raise HTTPException(status_code=400, detail="Invalid action")

        # Проверяем здоровье игрока
        if player_data["health"] <= 0:
            await client.delete(f"{STORAGE_SERVICE}/player/{player_id}")
            result.success = False
            result.message += ". Вы погибли!"
            return result

        # Обновляем данные игрока
        await client.put(f"{STORAGE_SERVICE}/player/{player_id}", json=player_data)
        return result
