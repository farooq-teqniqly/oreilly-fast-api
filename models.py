from pydantic import BaseModel


class EmployeeModel(BaseModel):
    id: int
    name: str
    is_active: bool
    class Config:
        json_schema_extra = {
            "example": {
                "id": 200,
                "name": "Bob",
                "is_active": True,
            },
        }

class AddEmployeeModel(BaseModel):
    id: int
    name: str
    is_active: bool=False
    class Config:
        json_schema_extra = {
            "example": {
                "id": 200,
                "name": "Bob",
                "is_active": True,
            },
        }
