from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.board import PostCreate, PostModel, PostResponse
from app.db.mongodb import get_database
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.get("/", response_model=List[PostResponse])
async def get_posts():
    db = await get_database()
    posts = await db["posts"].find().sort("created_at", -1).to_list(100)
    
    # Convert _id to id for response
    results = []
    for post in posts:
        post["id"] = str(post["_id"])
        results.append(post)
    return results

@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate):
    db = await get_database()
    post_dict = post.dict()
    post_dict["created_at"] = datetime.utcnow()
    post_dict["updated_at"] = datetime.utcnow()
    
    new_post = await db["posts"].insert_one(post_dict)
    created_post = await db["posts"].find_one({"_id": new_post.inserted_id})
    
    created_post["id"] = str(created_post["_id"])
    return created_post

@router.get("/{id}", response_model=PostResponse)
async def get_post(id: str):
    db = await get_database()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    post = await db["posts"].find_one({"_id": ObjectId(id)})
    if post:
        post["id"] = str(post["_id"])
        return post
    raise HTTPException(status_code=404, detail="Post not found")

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(id: str):
    db = await get_database()
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ID format")
        
    delete_result = await db["posts"].delete_one({"_id": ObjectId(id)})
    
    if delete_result.deleted_count == 1:
        return
    raise HTTPException(status_code=404, detail="Post not found")
