from fastapi import FastAPI, Path

app = FastAPI()

@app.get(f"/employees/index")
async def index():
    return {"message": "This is the Employees API"}

@app.get("/employees/{id}")
async def get_employee_by_id(id: int=Path(
    ge=101, 
    le=999,
    title="Employee ID",
    description="ID of the employee",)):
    name = "Bob"
    return {"name": name, "id": id}

@app.get("/employees")
async def get_employees(is_active: bool=False):
    employees = [
        {"name": "Bob", "is_active": True},
        {"name": "Alice", "is_active": False},
        {"name": "Charlie", "is_active": True},
    ]
    
    return [employee for employee in employees if employee["is_active"] == is_active]