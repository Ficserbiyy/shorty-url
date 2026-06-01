from sqlmodel import SQLModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime


class UrlBase(SQLModel):
    url: str
    
class URL(UrlBase, table=True):
    id: int | None = Field(default=None, primary_key=True )
    shortcode: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    access_count: int = Field(default=0)
    
class UrlUpdate(SQLModel):
    url: str
    
class UrlResponse(UrlBase):
    shortcode: str
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    
class Settings(BaseSettings):
    DATABASE_URL: str = ''
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False
    )

settings = Settings()
    
    