import os
import sys
import shutil
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Make sure agents folder is importable
sys.path.append(os.path.dirname(__file__))

from database import load_csv_to_db, get_engine
from agents.cleaning_agent import run_cleaning_agent
from agents.sql_agent import run_sql_agent
from agents.forecast_agent import run_forecast_agent
from agents.anomaly_agent import run_anomaly_agent
from agents.report_agent import run_report_agent

app = FastAPI(
    title="AI Business Intelligence Analyst",
    description="Multi-agent AI system for business data analysis",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "./data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("./data", exist_ok=True)


# ── Request models ─────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "AI Business Intelligence Analyst API",
        "status": "running",
        "docs": "/docs",
    }


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV file → clean it → load into SQLite DB.
    Returns a cleaning report.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # Save uploaded file
    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Run cleaning agent
    result = run_cleaning_agent(save_path)
    report = result["report"]
    df_clean = result["dataframe"]

    # Save cleaned CSV
    clean_path = os.path.join(UPLOAD_DIR, f"clean_{file.filename}")
    df_clean.to_csv(clean_path, index=False)

    # Load into DB
    db_result = load_csv_to_db(clean_path, table_name="sales")

    return {
        "status": "success",
        "file": file.filename,
        "cleaning_report": report,
        "database": db_result,
    }


@app.get("/dashboard")
def get_dashboard():
    """
    Returns KPIs and chart data for the main dashboard.
    """
    engine = get_engine()

    try:
        df = pd.read_sql("SELECT * FROM sales", con=engine)
    except Exception:
        raise HTTPException(status_code=404, detail="No data loaded. Please upload a CSV first.")

    sales_col = next((c for c in df.columns if c == "sales"), None)
    profit_col = next((c for c in df.columns if c == "profit"), None)
    date_col = next((c for c in df.columns if "order_date" in c or (c == "date")), None)

    kpis = {
        "total_revenue": round(float(df[sales_col].sum()), 2) if sales_col else 0,
        "total_profit": round(float(df[profit_col].sum()), 2) if profit_col else 0,
        "total_orders": len(df),
        "unique_customers": int(df["customer_id"].nunique()) if "customer_id" in df.columns else 0,
        "profit_margin": 0,
    }

    if kpis["total_revenue"] > 0:
        kpis["profit_margin"] = round(kpis["total_profit"] / kpis["total_revenue"] * 100, 2)

    charts = {}

    # Sales by region
    if "region" in df.columns and sales_col:
        region_sales = df.groupby("region")[sales_col].sum().reset_index()
        charts["sales_by_region"] = region_sales.to_dict(orient="records")

    # Sales by category
    if "category" in df.columns and sales_col:
        cat_sales = df.groupby("category")[sales_col].sum().reset_index()
        charts["sales_by_category"] = cat_sales.to_dict(orient="records")

    # Monthly revenue trend
    if date_col and sales_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df["month"] = df[date_col].dt.to_period("M").astype(str)
        monthly = df.groupby("month")[sales_col].sum().reset_index()
        monthly.columns = ["month", "sales"]
        charts["monthly_revenue"] = monthly.to_dict(orient="records")

    # Top 10 products
    if "product_name" in df.columns and sales_col:
        top_products = (
            df.groupby("product_name")[sales_col]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        charts["top_products"] = top_products.to_dict(orient="records")

    # Segment breakdown
    if "segment" in df.columns and sales_col:
        seg = df.groupby("segment")[sales_col].sum().reset_index()
        charts["sales_by_segment"] = seg.to_dict(orient="records")

    return {"kpis": kpis, "charts": charts}


@app.post("/query")
def natural_language_query(request: QueryRequest):
    """
    Takes a natural language business question and returns an AI answer.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    answer = run_sql_agent(request.question)
    return {
        "question": request.question,
        "answer": answer,
    }


@app.get("/forecast")
def get_forecast(days: int = 30):
    """
    Returns historical sales + 30-day forecast.
    """
    result = run_forecast_agent(days=days)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.get("/anomalies")
def get_anomalies():
    """
    Detects and returns anomalous orders using IsolationForest.
    """
    result = run_anomaly_agent()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@app.post("/report/generate")
def generate_report():
    """
    Generates a PDF business report with KPIs + AI executive summary.
    """
    import traceback
    output_path = "./data/business_report.pdf"
    try:
        result = run_report_agent(output_path=output_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(exc)}\n{traceback.format_exc()}")

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "status": result["status"],
        "kpis": result["kpis"],
        "ai_summary": result["ai_summary"],
        "download_url": "/report/download",
    }


@app.get("/report/download")
def download_report():
    """
    Download the generated PDF report.
    """
    report_path = "./data/business_report.pdf"
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not generated yet. Call /report/generate first.")

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename="business_report.pdf",
    )