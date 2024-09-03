from fastapi import APIRouter, Path, Response, status

from models import AddEmployeeModel

router = APIRouter()

@router.get("/index")
async def index():
    return {"message": "This is the Employees API"}

@router.get("/{id}")
async def get_employee_by_id(id: int=Path(
    ge=101, 
    le=999,
    title="Employee ID",
    description="ID of the employee",)):
    name = "Bob"
    return {"name": name, "id": id}

employees = [
        {"id": 200, "name": "Bob", "is_active": True},
        {"id": 201, "name": "Alice", "is_active": False},
        {"id": 202, "name": "Charlie", "is_active": True},
    ]

@router.get("/")
async def get_employees(is_active: bool=False):
    return [employee for employee in employees if employee["is_active"] == is_active]

@router.post("/")
async def add_employee(employee:AddEmployeeModel, response:Response):
    employees.append(employee.model_dump())
    response.status_code = status.HTTP_201_CREATED
    return employee