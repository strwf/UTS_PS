import os
import pandas as pd
import numpy as np

class DynamicSystemEngine:
    def __init__(self, csv_path: str = "data/sales.csv"):
        self.csv_path = csv_path
        self.baseline_retail_sales = 1000.0
        self.baseline_retail_transfers = 1050.0
        self.baseline_warehouse_sales = 500.0
        self.data_loaded = False
        self._load_and_aggregate_data()

    def _load_and_aggregate_data(self):
        if not os.path.exists(self.csv_path):
            return

        try:
            df = pd.read_csv(self.csv_path)
            # Standardize column headers
            df.columns = [c.strip().upper() for c in df.columns]

            # Aggregate monthly totals across the entire dataset
            if set(['YEAR', 'MONTH', 'RETAIL SALES', 'RETAIL TRANSFERS', 'WAREHOUSE SALES']).issubset(df.columns):
                monthly = df.groupby(['YEAR', 'MONTH'])[['RETAIL SALES', 'RETAIL TRANSFERS', 'WAREHOUSE SALES']].sum().reset_index()
                
                if len(monthly) > 0:
                    self.baseline_retail_sales = float(monthly['RETAIL SALES'].mean())
                    self.baseline_retail_transfers = float(monthly['RETAIL TRANSFERS'].mean())
                    self.baseline_warehouse_sales = float(monthly['WAREHOUSE SALES'].mean())
                    self.data_loaded = True
        except Exception as e:
            print(f"Warning: Could not parse CSV ({e}). Using robust baseline defaults.")

    def run_simulation(
        self,
        months: int = 24,
        lead_time_supplier: int = 2,
        lead_time_transfer: int = 1,
        safety_stock_factor: float = 1.5,
        demand_shock_percent: float = 0.0,
        shock_start_month: int = 6,
        adjustment_time: float = 2.0
    ) -> dict:
        """
        Simulasi Sistem Dinamik Rantai Pasok (2-Tier System):
        - Stock 1: Warehouse Inventory (S_w)
        - Stock 2: Retail Store Inventory (S_r)
        - Integration: Euler Method (dt = 1 month)
        """
        # Historical baseline monthly demand rates
        base_r_sales = max(self.baseline_retail_sales, 1.0)
        base_w_sales = max(self.baseline_warehouse_sales, 0.0)
        base_transfers = max(self.baseline_retail_transfers, 1.0)

        # Target Stock levels (Safety Stock formulation)
        target_retail_stock = base_r_sales * safety_stock_factor * max(lead_time_transfer, 1)
        target_warehouse_stock = (base_transfers + base_w_sales) * safety_stock_factor * max(lead_time_supplier, 1)

        # Initial Stocks
        S_r = target_retail_stock
        S_w = target_warehouse_stock

        # Pipelines for delayed orders (Lead Time)
        supplier_pipeline = [base_transfers + base_w_sales] * max(lead_time_supplier, 1)

        # Result tracking arrays
        history = {
            "month": [],
            "warehouse_stock": [],
            "retail_stock": [],
            "retail_sales": [],
            "warehouse_sales": [],
            "supplier_inflow": [],
            "retail_transfers": [],
            "retail_demand": [],
            "warehouse_demand": [],
            "retail_stockout": [],
            "warehouse_stockout": []
        }

        for t in range(1, months + 1):
            # 1. Determine Demand Dynamics with Shock
            shock_multiplier = 1.0
            if t >= shock_start_month:
                shock_multiplier += (demand_shock_percent / 100.0)

            current_retail_demand = base_r_sales * shock_multiplier
            current_warehouse_demand = base_w_sales * shock_multiplier

            # 2. Flow: Inflow from Supplier (Arriving from pipeline delay)
            inflow_supplier = supplier_pipeline.pop(0)

            # 3. Flow: Transfer from Warehouse to Retail Store (Desired vs Actual Stock Available)
            desired_transfer = current_retail_demand + (target_retail_stock - S_r) / max(adjustment_time, 0.5)
            desired_transfer = max(0.0, desired_transfer)
            
            # Warehouse actual outflow capacity check
            actual_transfer = min(S_w, desired_transfer)
            
            # Warehouse direct sales execution
            remaining_w_stock = S_w - actual_transfer
            actual_w_sales = min(remaining_w_stock, current_warehouse_demand)

            # 4. Flow: Retail Store Outflow (Retail Sales)
            actual_r_sales = min(S_r + actual_transfer, current_retail_demand)

            # 5. Stockout calculation
            r_stockout = max(0.0, current_retail_demand - actual_r_sales)
            w_stockout = max(0.0, current_warehouse_demand - actual_w_sales)

            # 6. Inventory Replenishment Decision (Feedback Loop to Supplier)
            total_w_outflow_estimate = actual_transfer + actual_w_sales
            desired_supplier_order = total_w_outflow_estimate + (target_warehouse_stock - (S_w + sum(supplier_pipeline))) / max(adjustment_time, 0.5)
            desired_supplier_order = max(0.0, desired_supplier_order)

            # Push new order into supplier pipeline
            supplier_pipeline.append(desired_supplier_order)

            # 7. Euler State Integration (Update Stocks for t + 1)
            S_w = S_w + inflow_supplier - actual_transfer - actual_w_sales
            S_r = S_r + actual_transfer - actual_r_sales

            # Prevent negative stocks due to discretization edge cases
            S_w = max(0.0, S_w)
            S_r = max(0.0, S_r)

            # Record timestep data
            history["month"].append(t)
            history["warehouse_stock"].append(round(S_w, 2))
            history["retail_stock"].append(round(S_r, 2))
            history["retail_sales"].append(round(actual_r_sales, 2))
            history["warehouse_sales"].append(round(actual_w_sales, 2))
            history["supplier_inflow"].append(round(inflow_supplier, 2))
            history["retail_transfers"].append(round(actual_transfer, 2))
            history["retail_demand"].append(round(current_retail_demand, 2))
            history["warehouse_demand"].append(round(current_warehouse_demand, 2))
            history["retail_stockout"].append(round(r_stockout, 2))
            history["warehouse_stockout"].append(round(w_stockout, 2))

        return {
            "baseline": {
                "retail_sales": round(base_r_sales, 2),
                "retail_transfers": round(base_transfers, 2),
                "warehouse_sales": round(base_w_sales, 2),
                "data_loaded_from_csv": self.data_loaded
            },
            "simulation": history
        }