from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_filter import FilterDepends
from src.database import models as Models
from typing import Optional
from pydantic import Field
from sqlalchemy.orm import Query
from sqlalchemy import Select


class Pagination:
    def __init__(self, offset: int = 0, limit:int = 25):
        """
        @param limit: max - 250, default - 25
        """
        self.offset = offset
        self.limit = min(limit, 250)
    
    def paginate(self, query: Query | Select):
        return query.offset(self.offset).limit(self.limit)


class LogsFilter(Filter):
    order_by : list[str] = ["time"]
    search: Optional[str] = None

    class Constants(Filter.Constants):
        model = Models.ChatLog
        search_model_fields = ["text", "steamId", "server"]


class UserFilter(Filter):
    steam_id: Optional[str] = None

    class Constants(Filter.Constants):
        model = Models.User
        search_field_name = 'steam_id'
        search_model_fields = ['steamId']


class SeasonFilter(Filter):
    order_by: list[str] = ['date', 'agression', 'support', 'perks', 'id']
    search: Optional[str] = None
    user: Optional[UserFilter] = FilterDepends(UserFilter)
    
    class Constants(Filter.Constants):
        model = Models.ScoreSeason
        search_model_fields = ["date"]
 

class RoundScoreFilter(Filter):
    order_by: list[str] = ['time', 'agression', 'support', 'perks', 'id', 'team']
    search: Optional[str] = None
    user: Optional[UserFilter] = FilterDepends(UserFilter)

    class Constants(Filter.Constants):
        model = Models.RoundScore
        search_model_fields = ["time"]
        

class L4D2ItemFilter(Filter):
    order_by: list[str] = ['name', 'command', 'id']
    search: Optional[str] = None
    
    class Constants(Filter.Constants):
        model = Models.L4D2Item
        search_model_fields = ["name", 'command', 'id']
        

class PrivilegeItemFilter(Filter):
    order_by: list[str] = ['name', 'privilegeTypeId', 'id']
    search: Optional[str] = None
    
    class Constants(Filter.Constants):
        model = Models.PrivilegeItem
        search_model_fields = ["name", 'privilegeTypeId', 'id']


class AdditionalItemFilter(Filter):
    item: Optional[str] = None
    class Constants(Filter.Constants):
        model = Models.L4D2Item
        search_field_name = 'item'
        search_model_fields = ['name', 'command', 'id']


class UserInventoryFilter(Filter):
    order_by: list[str] = ['activeUntil', 'itemId', 'id', 'userId']
    search: Optional[str] = None
    user: Optional[UserFilter] = FilterDepends(UserFilter)
    item: Optional[AdditionalItemFilter] = FilterDepends(AdditionalItemFilter)
    
    class Constants(Filter.Constants):
        model = Models.UserInventory
        search_model_fields = ["activeUntil", "id"]
    