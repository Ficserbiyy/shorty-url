from sqlmodel import SQLModel
from models import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


engine = create_async_engine(settings.DATABASE_URL)#, echo=True) # Optional

async_session_factory = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_session():
    async with async_session_factory() as session:
        yield session
           
        
async def create_db_and_tables():
    """Create database tables based on SQLModel schemas."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        
        
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def encode_base62(num: int) -> str:
    if num == 0:
        return ALPHABET[0]
    arr = []
    base = len(ALPHABET)
    while num:
        num, rem = divmod(num, base)
        arr.append(ALPHABET[rem])
    arr.reverse()
    return ''.join(arr)
