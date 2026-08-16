from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session

# depends可以帮我们自动调用函数并注入参数
DbSession = Annotated[AsyncSession, Depends(get_session)]
