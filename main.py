from fastapi import FastAPI, Depends, HTTPException, Request
from sqlmodel import select
from typing import Final
import redis.asyncio as redis
from dbLogic import get_session, create_db_and_tables, AsyncSession, engine, encode_base62
from contextlib import asynccontextmanager
from models import URL, UrlBase, UrlResponse, settings
from fastapi.responses import RedirectResponse
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
    await engine.dispose()       


app: Final = FastAPI(lifespan=lifespan)
redis_client: Final = redis.from_url(settings.REDIS_URL, decode_responses=True)

origins: Final = [
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)


@app.post('/shorten', response_model=UrlResponse, status_code=201)
async def short_url(
    url_data: UrlBase,
    request: Request, 
    session: AsyncSession = Depends(get_session)
):
    '''Create Short URL'''
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
    
@app.get('/{shortcode}') # Unnecessary endpoint
async def redirect_to_url(shortcode: str, session: AsyncSession = Depends(get_session)):
    '''Redirect to Original URL'''
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
    

@app.get('/shorten/{shortcode}/stats', response_model=UrlResponse, status_code=200)
@app.get('/shorten/{shortcode}', response_model=UrlResponse, status_code=200)
async def get_url_info(
    shortcode: str, 
    session: AsyncSession = Depends(get_session)
):
    '''Retrieve Original URL and URL statistics from a short URL'''
    statement = select(URL).where(URL.shortcode == shortcode)
    result = await session.execute(statement)
    db_url = result.scalars().first()
    
    if not db_url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    clicks = await redis_client.get(f"stats:{shortcode}")
    
    if clicks is not None:
        db_url.access_count = int(clicks)
        session.add(db_url)
        await session.commit()
    return db_url



@app.delete('/shorten/{shortcode}', status_code=204)
async def delete_url(
    shortcode: str, 
    session: AsyncSession = Depends(get_session)
):
    '''Delete Short URL'''
    statement = select(URL).where(URL.shortcode == shortcode)
    result = await session.execute(statement)
    db_url = result.scalars().first()
    
    if not db_url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    await session.delete(db_url)
    await session.commit()
    
    await redis_client.delete(f"url:{shortcode}")
    await redis_client.delete(f"stats:{shortcode}")
    return None



@app.put('/shorten/{shortcode}', response_model=UrlResponse, status_code=200)
async def update_url(
    shortcode: str, 
    url_update: UrlBase, 
    session: AsyncSession = Depends(get_session)
):
    '''Update Short URL'''
    statement = select(URL).where(URL.shortcode == shortcode)
    result = await session.execute(statement)
    db_url = result.scalars().first()
    
    if not db_url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    db_url.url = url_update.url
    db_url.updated_at = datetime.utcnow()
    
    session.add(db_url)
    await session.commit()
    await session.refresh(db_url)

    await redis_client.set(f"url:{shortcode}", db_url.url)
    return db_url