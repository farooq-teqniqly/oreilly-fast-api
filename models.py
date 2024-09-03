from pydantic import BaseModel

class AddEmployeeModel(BaseModel):
    id: int
    name: str
    is_active: bool=False