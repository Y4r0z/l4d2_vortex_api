from fastapi_filter.contrib.sqlalchemy import Filter
from src.database import crud as Crud, models as Models
from src.types import api_models as Schemas
from typing import Optional
from sqlalchemy.orm import Session, Query
from fastapi import Depends
from src.api.tools import get_db
from typing import TypeVar

from fastapi_filter import FilterDepends


class LogsFilter(Filter):
    order_by : list[str] = ["time"]
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Models.ChatLog
        search_model_fields = ["text", "steamId", "server"]
    
class Pagination:
    def __init__(self, offset: int = 0, limit:int = 25):
        self.offset = offset
        self.limit = limit