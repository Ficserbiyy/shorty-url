from sqlmodel import SQLModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime


class UrlBase(SQLModel):
    '''To create or update a URL'''
    url: str
    
class URL(UrlBase, table=True):
    id: int | None = Field(default=None, primary_key=True )
    shortcode: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(default=0)

class UrlResponse(UrlBase):
    id: int
    shortcode: str
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    
class Settings(BaseSettings):
    ''' Enviroment settings '''
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password" ## Not your password
    DB_HOST: str = "db" 
    DB_NAME: str = "shorty"
    REDIS_URL: str = 'redis://redis:6379'
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False
    )
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"

settings = Settings()