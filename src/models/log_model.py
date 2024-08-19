from typing import List
from sqlalchemy import Column, String, Float, JSON

from src.models.base_model import BaseModel


ANGLES = {
    "0": "Frente",
    "45": "Frente + Lateral do Motorista",
    "90": "Lateral do Motorista",
    "135": "Traseira + Lateral do Motorista",
    "180": "Traseira",
    "225": "Traseira + Lateral do Passageiro",
    "270": "Lateral do Passageiro",
    "315": "Frente + Lateral do Passageiro",
}


class LogModel(BaseModel):
    __tablename__ = 'logs'

    identifier = Column(String, nullable=False)
    ias = Column(JSON, nullable=False)
    product = Column(String, nullable=False)
    plate = Column(String, nullable=False)
    angle = Column(String, nullable=True)
    result = Column(JSON, nullable=True)
    runtime = Column(Float, default=0)

    @property
    def result_plate(self):
        return self.result.get("plate", {}).get("result", "-")
    
    @property
    def angle_display(self):
        if self.angle:
            return ANGLES.get(self.angle)
        return "-"
    
    @property
    def result_angle(self):
        if angle := self.result.get("angle", {}).get("result"):
            return ANGLES.get(angle)
        return "-"

    @property
    def match_plate(self):
        return self.plate == self.result_plate
    
    @property
    def match_angle(self):
        return self.angle == self.result.get("angle", {}).get("result")

    @property
    def plate_thumb(self):
        if thumb := self.result.get("plate", {}).get("thumb"):
            return f"data:image/jpg;base64,{ thumb }"
        return ""
        
    @property
    def angle_thumb(self):
        if thumb := self.result.get("angle", {}).get("thumb"):
            return f"data:image/jpg;base64,{ thumb }"
        return ""
    
    def get_json_fields(self) -> List[str]:
        return [
            "id",
            "created_at",
            "identifier",
            "ias",
            "product",
            "plate",
            "angle",
            "runtime",
            "result",
        ]
