from fastapi import FastAPI
from routers import employees

app = FastAPI()

app.include_router(employees.router, prefix="/employees", tags=["Employees"])