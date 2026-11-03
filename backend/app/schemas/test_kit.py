from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TestKitProfileBase(BaseModel):
    profile_version: str
    validation_status: str
    reference_source: str
    approval_details: Optional[str] = None
    positive_cielab_l: float
    positive_cielab_a: float
    positive_cielab_b: float
    positive_delta_e_threshold: float = 18.0
    negative_cielab_l: float
    negative_cielab_a: float
    negative_cielab_b: float
    negative_delta_e_threshold: float = 20.0
    inconclusive_delta_e_threshold: float = 8.0
    reaction_roi_x: float = 0.35
    reaction_roi_y: float = 0.25
    reaction_roi_w: float = 0.58
    reaction_roi_h: float = 0.55

class TestKitProfileCreate(TestKitProfileBase):
    kit_id: int

class TestKitProfileResponse(TestKitProfileBase):
    id: int
    kit_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class TestKitBase(BaseModel):
    name: str
    manufacturer: str
    model_number: str
    analyte: str
    reaction_time_seconds: int = 60
    instructions: Optional[str] = None
    is_active: bool = True

class TestKitCreate(TestKitBase):
    pass

class TestKitResponse(TestKitBase):
    id: int
    created_at: datetime
    profiles: List[TestKitProfileResponse] = []

    class Config:
        from_attributes = True

class CalibrationCardResponse(BaseModel):
    id: int
    name: str
    card_type: str
    layout_json: str
    is_active: bool

    class Config:
        from_attributes = True
