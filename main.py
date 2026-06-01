from fastapi import FastAPI, Depends, HTTPException, Request, status
from sqlmodel import select
from typing import Final, List
from Logic import encode_base62
from sqlalchemy.orm import joinedload
import redis.asyncio as redis
import json
from fastapi.encoders import jsonable_encoder
from dbLogic import get_session, create_db_and_tables, AsyncSession, engine
from contextlib import asynccontextmanager
from models import URL, UrlBase, UrlResponse, UrlUpdate
from fastapi.responses import RedirectResponse



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
    request: Request, 
    session: AsyncSession = Depends(get_session)
):
    'Create Short URL'
    client_ip = request.client.host if request.client else "127.0.0.1"
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
    
    assert db_url.id is not None 
    shortcode = encode_base62(db_url.id)
    db_url.shortcode = shortcode
    
    session.add(db_url)
    await session.commit()
    await redis_client.set(f"url:{shortcode}", db_url.url)
    return db_url
    
@app.get('/{shortcode}')
async def redirect_to_url(shortcode: str, session: AsyncSession = Depends(get_session)):
    'Redirect to Original URL'
    cached_url = await redis_client.get(f"url:{shortcode}")
    if cached_url:
        if isinstance(cached_url, str):
            await redis_client.incr(f"stats:{shortcode}")
            return RedirectResponse(url=cached_url)
    statement = select(URL).where(URL.shortcode == shortcode)
    result = await session.execute(statement)
    
    db_url = result.scalars().first() 
    if not db_url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    await redis_client.set(f"url:{shortcode}", db_url.url)
    await redis_client.incr(f"stats:{shortcode}")
    return RedirectResponse(url=db_url.url)
    

