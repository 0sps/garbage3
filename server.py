from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import csv
import os
import time

app = FastAPI()

# Allow CORS for development convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "all_trades.csv"

def read_trades():
    if not os.path.exists(DATA_FILE):
        return []
    
    trades = []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append(row)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []
        
    # Sort by timestamp descending
    trades.sort(key=lambda x: float(x['timestamp']), reverse=True)
    return trades

@app.get("/api/trades")
def get_trades():
    return read_trades()

# Serve static files (Frontend)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
