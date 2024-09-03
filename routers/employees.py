from typing import List
from fastapi import APIRouter, HTTPException, Path, Response, status

from models import AddEmployeeModel, EmployeeModel

router = APIRouter()

@router.get("/index")
async def index():
    return {"message": "This is the Employees API"}

employees = [
        {"id": 200, "name": "Bob", "is_active": True},
        {"id": 201, "name": "Alice", "is_active": False},
        {"id": 202, "name": "Charlie", "is_active": True},
    ]

@router.get("/{id}", response_model=EmployeeModel, responses={404: {"description": "Employee not found"}})
async def get_employee_by_id(id: int=Path(
    ge=101, 
    le=999,
    title="Employee ID",
    description="ID of the employee",)):
    name = "Bob"
    matching_employees = [employee for employee in employees if employee["id"] == id]
    
    if matching_employees:
        return matching_employees[0]
    
    raise HTTPException(status_code=404, detail=f"Employee with id {id} not found")



@router.get("/", response_model=List[EmployeeModel])
async def get_employees(is_active: bool=False):
    return [employee for employee in employees if employee["is_active"] == is_active]

@router.post("/", response_model=List[EmployeeModel], status_code=status.HTTP_201_CREATED)
async def add_employee(employee:AddEmployeeModel):
    employees.append(employee.model_dump())
    return employee