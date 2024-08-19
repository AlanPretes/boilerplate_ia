from collections import OrderedDict
from datetime import datetime
from typing import List
from uuid import uuid4

import pytz
from sqlalchemy import Column, String, DateTime, Boolean

from src.configs.database import db


class BaseModel(db.Model):
    __abstract__ = True

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    @property
    def created_at_display(self):
        self.created_at = self.created_at.replace(tzinfo=pytz.utc)
        self.created_at = self.created_at.astimezone(pytz.timezone('America/Sao_Paulo'))
        return self.created_at.strftime("%d/%m/%Y %H:%M")
    
    def get_json_fields(self) -> List[str]:
        raise NotImplementedError()

    def to_json(self):
        result = OrderedDict()
        json_fields = self.get_json_fields()

        for field in json_fields:
            if hasattr(self, field):
                result[field] = getattr(self, field)

        return result