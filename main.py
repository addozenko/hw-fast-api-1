from datetime import datetime, timezone
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Path, Query, Depends
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from models import AdvertisementORM, AsyncSessionLocal, init_db
from sqlalchemy import select


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

def orm_to_pydantic(ad: AdvertisementORM) -> Advertisement:
    return Advertisement(
        id=ad.id,
        title=ad.title,
        description=ad.description,
        price=ad.price,
        author=ad.author,
        created_at=ad.created_at,
    )

async def get_session() :
    async with AsyncSessionLocal() as session:
        yield session

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/advertisement", response_model=Advertisement, status_code=201)
async def create_advertisement(ad: AdvertisementCreate, session: AsyncSession = Depends(get_session)):
    new_id = uuid4()
    ad_obj = AdvertisementORM(
        id=new_id,
        title=ad.title,
        description=ad.description,
        price=ad.price,
        author=ad.author,
        created_at=datetime.now(timezone.utc),
    )
    session.add(ad_obj)
    await session.commit()
    await session.refresh(ad_obj)
    return orm_to_pydantic(ad_obj)

@app.get("/advertisement/{advertisement_id}", response_model=Advertisement)
async def get_advertisement(advertisement_id: UUID = Path(..., description="ID объявления"), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(AdvertisementORM).where(AdvertisementORM.id == advertisement_id))
    ad_obj = result.scalar_one_or_none()
    if ad_obj is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    return orm_to_pydantic(ad_obj)

@app.patch("/advertisement/{advertisement_id}", response_model=Advertisement)
async def update_advertisement(
    advertisement_id: UUID = Path(..., description="ID объявления"),
    ad_update: AdvertisementUpdate = ...,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(AdvertisementORM).where(AdvertisementORM.id == advertisement_id))
    existing = result.scalar_one_or_none()
    if existing is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")

    update_data = ad_update.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(existing, k, v)

    session.add(existing)
    await session.commit()
    await session.refresh(existing)
    return orm_to_pydantic(existing)

@app.delete("/advertisement/{advertisement_id}", status_code=204)
async def delete_advertisement(advertisement_id: UUID = Path(..., description="ID объявления"), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(AdvertisementORM).where(AdvertisementORM.id == advertisement_id))
    ad_obj = result.scalar_one_or_none()
    if ad_obj is None:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    await session.delete(ad_obj)
    await session.commit()
    return

@app.get("/advertisement", response_model=List[Advertisement])
async def search_advertisements(
    q: Optional[str] = Query(None, description="Поиск по заголовку и описанию"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    author: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    stmt = select(AdvertisementORM)
    ads = (await session.execute(stmt)).scalars().all()

    results = ads

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

    return [orm_to_pydantic(a) for a in results]