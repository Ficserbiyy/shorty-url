from fastapi import FastAPI, Depends, HTTPException, Request, status
from typing import Final
from Logic import encode_base62
from sqlalchemy.orm import joinedload
import redis.asyncio as redis
import json
from fastapi.encoders import jsonable_encoder
from dbLogic import get_session, create_db_and_tables, AsyncSession, engine
from contextlib import asynccontextmanager
from models import URL, UrlBase, UrlResponse, UrlUpdate




@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
    await engine.dispose()       


app: Final = FastAPI(lifespan=lifespan)
redis_client: Final = redis.from_url("redis://localhost:6379", decode_responses=True)



@app.post('/shorten', response_model=UrlResponse)
async def short_url(
    url_data: UrlBase, 
    session: AsyncSession = Depends(get_session),
    request: Request
):
    client_ip = request.client.host
    limit_key = f"limit:urls:{client_ip}"
    current_count = await redis_client.incr(limit_key)
    
    if current_count == 1:
        await redis_client.expire(limit_key, 60)
    if current_count > 10:
        raise HTTPException(status_code=429, detail="Too many requests")
    
    db_url = URL(url=url_data.url, shortcode="")
    session.add(db_url)
    await session.commit()
    await session.refresh(db_url)
    
    shortcode = encode_base62(db_url.id)
    db_url.shortcode = shortcode
    
    session.add(db_url)
    await session.commit()
    await redis_client.set(f"url:{shortcode}", db_url.url)
    return db_url
    
    

