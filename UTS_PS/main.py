from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from engine.system_dynamics import DynamicSystemEngine

app = FastAPI(
    title="Warehouse & Retail Supply Chain System Dynamics",
    description="Dynamic System Simulation Web Application for UTS Pemodelan & Simulasi",
    version="1.0.0"
)

# Initialize engine instance
engine = DynamicSystemEngine(csv_path="data/sales.csv")

@app.get("/api/simulate")
def run_simulation(
    months: int = Query(24, ge=6, le=60),
    lead_time_supplier: int = Query(2, ge=1, le=12),
    lead_time_transfer: int = Query(1, ge=1, le=6),
    safety_stock_factor: float = Query(1.5, ge=0.5, le=4.0),
    demand_shock_percent: float = Query(0.0, ge=-50.0, le=100.0),
    shock_start_month: int = Query(6, ge=1, le=48),
    adjustment_time: float = Query(2.0, ge=0.5, le=10.0)
):
    results = engine.run_simulation(
        months=months,
        lead_time_supplier=lead_time_supplier,
        lead_time_transfer=lead_time_transfer,
        safety_stock_factor=safety_stock_factor,
        demand_shock_percent=demand_shock_percent,
        shock_start_month=shock_start_month,
        adjustment_time=adjustment_time
    )
    return results

# Serve Static files (HTML, CSS, JS)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    return {"message": "Dynamic System Engine API Running. Static UI not found."}