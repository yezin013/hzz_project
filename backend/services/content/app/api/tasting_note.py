from fastapi import APIRouter, HTTPException, Body
from typing import List
from app.db.mongodb import get_database
from app.models.tasting_note import TastingNoteCreate, TastingNoteResponse, PyObjectId
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.post("", response_model=TastingNoteResponse)
async def create_tasting_note(note: TastingNoteCreate):
    db = await get_database()
    note_dict = note.dict()
    
    # Insert into MongoDB
    new_note = await db["tasting_notes"].insert_one(note_dict)
    
    created_note = await db["tasting_notes"].find_one({"_id": new_note.inserted_id})
    created_note["_id"] = str(created_note["_id"]) # Standardize for Pydantic
    return created_note

@router.get("/user/{user_id}", response_model=List[TastingNoteResponse])
async def get_user_tasting_notes(user_id: str):
    db = await get_database()
    notes = await db["tasting_notes"].find({"user_id": user_id}).to_list(1000)
    for note in notes:
        note["_id"] = str(note["_id"])
    return notes

@router.get("", response_model=List[TastingNoteResponse])
async def get_all_public_notes(limit: int = 20):
    db = await get_database()
    # Sort by created_at desc
    # TODO: Ensure index on created_at field for performance
    cursor = db["tasting_notes"].find({"is_public": True}).sort("created_at", -1).limit(limit)
    notes = await cursor.to_list(limit)
    
    # helper to fix _id
    for note in notes:
        note["_id"] = str(note["_id"])
        
    return notes

@router.get("/liquor/{liquor_id}", response_model=List[TastingNoteResponse])
async def get_liquor_tasting_notes(liquor_id: int):
    db = await get_database()
    # Filter for public notes only
    notes = await db["tasting_notes"].find({"liquor_id": liquor_id, "is_public": True}).to_list(1000)
    return notes

@router.delete("/{note_id}")
async def delete_tasting_note(note_id: str):
    db = await get_database()
    
    if not ObjectId.is_valid(note_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    result = await db["tasting_notes"].delete_one({"_id": ObjectId(note_id)})
    
    if result.deleted_count == 1:
        return {"message": "Tasting note deleted"}
    raise HTTPException(status_code=404, detail="Note not found")

@router.put("/{note_id}", response_model=TastingNoteResponse)
async def update_tasting_note(note_id: str, note: TastingNoteCreate):
    db = await get_database()
    
    if not ObjectId.is_valid(note_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    note_dict = note.dict()
    # Don't update created_at, update updated_at
    note_dict["updated_at"] = datetime.utcnow()
    
    result = await db["tasting_notes"].update_one(
        {"_id": ObjectId(note_id)},
        {"$set": note_dict}
    )
    
    if result.matched_count == 1:
        updated_note = await db["tasting_notes"].find_one({"_id": ObjectId(note_id)})
        updated_note["_id"] = str(updated_note["_id"])
        return updated_note
        
    raise HTTPException(status_code=404, detail="Note not found")

@router.post("/{note_id}/like")
async def toggle_like(note_id: str, user_data: dict = Body(...)):
    """
    Toggle like status for a user.
    Body: {"user_id": "google_12345"}
    """
    db = await get_database()
    user_id = user_data.get("user_id")
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    if not ObjectId.is_valid(note_id):
        raise HTTPException(status_code=400, detail="Invalid ID format")

    note = await db["tasting_notes"].find_one({"_id": ObjectId(note_id)})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    liked_by = note.get("liked_by", [])
    
    if user_id in liked_by:
        # Unlike
        await db["tasting_notes"].update_one(
            {"_id": ObjectId(note_id)},
            {"$pull": {"liked_by": user_id}}
        )
        is_liked = False
    else:
        # Like
        await db["tasting_notes"].update_one(
            {"_id": ObjectId(note_id)},
            {"$addToSet": {"liked_by": user_id}}
        )
        is_liked = True

    # Return updated count and status
    updated_note = await db["tasting_notes"].find_one({"_id": ObjectId(note_id)})
    return {
        "is_liked": is_liked,
        "like_count": len(updated_note.get("liked_by", [])),
        "liked_by": updated_note.get("liked_by", [])
    }
