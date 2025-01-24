from fastapi import FastAPI, HTTPException
import httpx
from typing import Dict, List
from pydantic import BaseModel

app = FastAPI()

STORAGE_SERVICE = "http://storage-service:8001"

@app.post("/inventory/{player_id}/add")
async def add_item(player_id: str, item: str):
    async with httpx.AsyncClient() as client:
        # Получаем текущие данные игрока
        response = await client.get(f"{STORAGE_SERVICE}/player/{player_id}")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player_data = response.json()
        player_data["inventory"].append(item)
        
        # Обновляем данные игрока
        await client.put(f"{STORAGE_SERVICE}/player/{player_id}", json=player_data)
        return {"status": "success", "message": f"Item {item} added to inventory"}

@app.post("/inventory/{player_id}/use")
async def use_item(player_id: str, item: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{STORAGE_SERVICE}/player/{player_id}")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Player not found")
        
        player_data = response.json()
        if item not in player_data["inventory"]:
            raise HTTPException(status_code=404, detail="Item not found in inventory")
        
        # Применяем эффект предмета
        if item == "зелье":
            player_data["mana"] += 10
            player_data["inventory"].remove(item)
        elif item == "руна":
            player_data["health"] += 50
            player_data["inventory"].remove(item)
            
        # Обновляем данные игрока
        await client.put(f"{STORAGE_SERVICE}/player/{player_id}", json=player_data)
        return {"status": "success", "message": f"Item {item} used"}
