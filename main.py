from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Path, Query
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

app = FastAPI(title="Advertisements API")

class AdvertisementCreate(BaseModel):
    title: str = Field(..., example="Продаю велосипед")
    description: str = Field(..., example="Чистый вагон, состояние отличное")
    price: float = Field(..., ge=0, example=15000.0)
    author: str = Field(..., example="Иван Иванов")

class AdvertisementUpdate(BaseModel):
    title: Optional[str] = Field(None, example="Продаю велосипед")
    description: Optional[str] = Field(None, example="Чистый вагон, состояние отличное")
    price: Optional[float] = Field(None, ge=0, example=15000.0)
    author: Optional[str] = Field(None, example="Иван Иванов")

class Advertisement(BaseModel):
    id: UUID
    title: str
    description: str
    price: float
    author: str
    created_at: datetime


ads_db: dict[UUID, Advertisement] = {}

def current_time() -> datetime:
    return datetime.now(timezone.utc)

@app.post("/advertisement", response_model=Advertisement, status_code=201)
def create_advertisement(ad: AdvertisementCreate):
    new_id = uuid4()
    ad_obj = Advertisement(
        id=new_id,
        title=ad.title,
        description=ad.description,
        price=ad.price,
        author=ad.author,
        created_at=current_time(),
    )
    ads_db[new_id] = ad_obj
    return ad_obj

@app.get("/advertisement/{advertisement_id}", response_model=Advertisement)
def get_advertisement(advertisement_id: UUID = Path(..., description="ID объявления")):
    if advertisement_id not in ads_db:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return ads_db[advertisement_id]

@app.patch("/advertisement/{advertisement_id}", response_model=Advertisement)
def update_advertisement(
    advertisement_id: UUID = Path(..., description="ID объявления"),
    ad_update: AdvertisementUpdate = ...
):
    if advertisement_id not in ads_db:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    existing = ads_db[advertisement_id]
    update_data = ad_update.dict(exclude_unset=True)
    updated = existing.copy()
    for k, v in update_data.items():
        setattr(updated, k, v)
    ads_db[advertisement_id] = updated
    return updated

@app.delete("/advertisement/{advertisement_id}", status_code=204)
def delete_advertisement(advertisement_id: UUID = Path(..., description="ID объявления")):
    if advertisement_id not in ads_db:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    del ads_db[advertisement_id]
    return

@app.get("/advertisement", response_model=List[Advertisement])
def search_advertisements(
    q: Optional[str] = Query(None, description="Поиск по заголовку и описанию"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    author: Optional[str] = Query(None)
):
    results = list(ads_db.values())

    if q:
        q_lower = q.lower()
        results = [
            a for a in results
            if q_lower in a.title.lower() or q_lower in a.description.lower()
        ]
    if min_price is not None:
        results = [a for a in results if a.price >= min_price]
    if max_price is not None:
        results = [a for a in results if a.price <= max_price]
    if author is not None:
        results = [a for a in results if a.author == author]

    return results