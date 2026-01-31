from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
from app.db.mongodb import get_database
from bson import ObjectId
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()


class FavoriteCreate(BaseModel):
    user_id: str
    drink_id: int
    drink_name: str
    image_url: Optional[str] = None


class FavoriteResponse(BaseModel):
    id: str
    user_id: str
    drink_id: int
    drink_name: str
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        json_encoders = {ObjectId: str}


@router.post("", response_model=FavoriteResponse)
async def add_favorite(favorite: FavoriteCreate):
    """Add a drink to user's favorites"""
    db = await get_database()
    
    # Check if already favorited
    existing = await db["favorites"].find_one({
        "user_id": favorite.user_id,
        "drink_id": favorite.drink_id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Already favorited")
    
    favorite_dict = favorite.dict()
    favorite_dict["created_at"] = datetime.utcnow()
    
    result = await db["favorites"].insert_one(favorite_dict)
    created = await db["favorites"].find_one({"_id": result.inserted_id})
    
    return {
        "id": str(created["_id"]),
        "user_id": created["user_id"],
        "drink_id": created["drink_id"],
        "drink_name": created["drink_name"],
        "image_url": created.get("image_url"),
        "created_at": created["created_at"]
    }


@router.delete("/{drink_id}")
async def remove_favorite(drink_id: int, user_data: dict = Body(...)):
    """Remove a drink from user's favorites"""
    db = await get_database()
    user_id = user_data.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    
    result = await db["favorites"].delete_one({
        "user_id": user_id,
        "drink_id": drink_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    return {"message": "Favorite removed", "drink_id": drink_id}


@router.get("/user/{user_id}", response_model=List[FavoriteResponse])
async def get_user_favorites(user_id: str):
    """Get all favorites for a user"""
    db = await get_database()
    
    cursor = db["favorites"].find({"user_id": user_id}).sort("created_at", -1)
    favorites = await cursor.to_list(1000)
    
    return [
        {
            "id": str(fav["_id"]),
            "user_id": fav["user_id"],
            "drink_id": fav["drink_id"],
            "drink_name": fav["drink_name"],
            "image_url": fav.get("image_url"),
            "created_at": fav["created_at"]
        }
        for fav in favorites
    ]


@router.get("/check/{user_id}/{drink_id}")
async def check_favorite(user_id: str, drink_id: int):
    """Check if a drink is favorited by user"""
    db = await get_database()
    
    existing = await db["favorites"].find_one({
        "user_id": user_id,
        "drink_id": drink_id
    })
    
    return {"is_favorited": existing is not None}


@router.post("/toggle")
async def toggle_favorite(favorite: FavoriteCreate):
    """Toggle favorite status - add if not exists, remove if exists"""
    db = await get_database()
    
    existing = await db["favorites"].find_one({
        "user_id": favorite.user_id,
        "drink_id": favorite.drink_id
    })
    
    if existing:
        # Remove favorite
        await db["favorites"].delete_one({"_id": existing["_id"]})
        return {
            "action": "removed",
            "is_favorited": False,
            "drink_id": favorite.drink_id
        }
    else:
        # Add favorite
        favorite_dict = favorite.dict()
        favorite_dict["created_at"] = datetime.utcnow()
        result = await db["favorites"].insert_one(favorite_dict)
        
        return {
            "action": "added",
            "is_favorited": True,
            "drink_id": favorite.drink_id,
            "id": str(result.inserted_id)
        }
