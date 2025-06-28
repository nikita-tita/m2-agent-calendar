from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

Base = declarative_base()

# Глобальная переменная для пула сессий
async_session_pool = None

async def create_pool(db_url: str) -> async_sessionmaker[AsyncSession]:
    global async_session_pool
    engine = create_async_engine(db_url, echo=False)
    
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
        
    async_session_pool = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )
    return async_session_pool

async def get_async_session() -> AsyncSession:
    """Dependency для получения асинхронной сессии базы данных"""
    if async_session_pool is None:
        # Инициализируем пул если он еще не создан
        await create_pool(settings.DATABASE_URL)
    
    async with async_session_pool() as session:
        yield session 