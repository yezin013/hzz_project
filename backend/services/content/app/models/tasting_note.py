from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class FlavorProfile(BaseModel):
    sweet: int = Field(..., ge=1, le=5, description="단맛")
    sour: int = Field(..., ge=1, le=5, description="신맛")
    body: int = Field(..., ge=1, le=5, description="바디감")
    scent: int = Field(..., ge=1, le=5, description="향")
    throat: int = Field(..., ge=1, le=5, description="목넘김")

class TastingNoteBase(BaseModel):
    user_id: str = Field(..., description="Cognito User Sub ID")
    liquor_id: int = Field(..., description="Traditional Liquor ID from MariaDB/ES")
    liquor_name: str = Field(..., description="Name of the liquor for display")
    rating: float = Field(..., ge=1, le=5.0, description="Star rating (0.5-5.0)")
    flavor_profile: FlavorProfile
    content: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list, description="List of image URLs")
    is_public: bool = Field(default=True, description="Publicly visible in community")
    author_name: str = Field(default="Unknown", description="User nickname or name")
    
    # 🆕 New Fields for Community Filter
    drinking_temperature: Optional[str] = Field(None, description="Recommended drinking temperature")
    pairing_foods: List[str] = Field(default_factory=list, description="Food pairings")
    atmosphere: Optional[str] = Field(None, description="Recommended atmosphere")
    seasons: List[str] = Field(default_factory=list, description="Recommended seasons")
    purchase_location: Optional[str] = Field(None, description="Where to buy")
    liked_by: List[str] = Field(default_factory=list, description="List of user IDs who liked this note")

class TastingNoteCreate(TastingNoteBase):
    pass

class TastingNoteResponse(TastingNoteBase):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    like_count: int = 0

    @classmethod
    def from_mongo(cls, doc):
        doc["id"] = str(doc["_id"])
        return cls(**doc)

    class Config:
        populate_by_name = True # Pydantic v2 support
        allow_population_by_field_name = True # Pydantic v1 support
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        schema_extra = {
            "example": {
                "user_id": "google_12345",
                "author_name": "홍길동",
                "liquor_id": 101,
                "liquor_name": "복순도가 손막걸리",
                "rating": 4.5,
                "flavor_profile": {
                    "sweet": 3,
                    "sour": 4,
                    "body": 2,
                    "scent": 5,
                    "throat": 3
                },
                "content": "톡 쏘는 탄산이 매력적임. 비오는 날 파전이랑 딱!",
                "tags": ["#스파클링", "#비오는날"],
                "is_public": True
            }
        }
