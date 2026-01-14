import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from database import db, create_document, get_documents
from schemas import Booking

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")

def send_to_airtable(booking_data: dict):
    if not AIRTABLE_API_KEY:
        print("Warning: AIRTABLE_API_KEY not set, skipping Airtable")
        return None
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    airtable_record = {
        "fields": {
            "First Name": booking_data.get("name", ""),
            "Email": booking_data.get("email", ""),
            "Company Website": booking_data.get("company_website", ""),
            "Service of Interest": booking_data.get("services", ""),
            "Project Timeline": booking_data.get("timeline", ""),
            "Business challenge you want to address with AI": booking_data.get("challenge", ""),
            "Estimated Budget for this Project": booking_data.get("budget", "")
        }
    }
    try:
        response = requests.post(url, json=airtable_record, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Airtable error: {e}")
        return None

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.post("/api/bookings")
def create_booking(booking: Booking):
    booking_dict = booking.model_dump()
    inserted_id = None

    # Try to save to database if available
    if db is not None:
        try:
            inserted_id = create_document("booking", booking)
        except Exception as e:
            print(f"Database error (non-fatal): {e}")

    # Always send to Airtable
    airtable_result = send_to_airtable(booking_dict)

    if airtable_result is None and inserted_id is None:
        raise HTTPException(status_code=500, detail="Failed to save booking")

    return {"status": "ok", "id": inserted_id or "airtable-only"}

@app.get("/api/bookings", response_model=List[dict])
def list_bookings(limit: int = 50):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        docs = get_documents("booking", {}, limit)
        for d in docs:
            if "_id" in d:
                d["_id"] = str(d["_id"])
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
def test_database():
    response = {
        "backend": "Running",
        "database": "Not Available",
        "database_url": None,
        "database_name": None,
    }
    try:
        if db is not None:
            response["database"] = "Connected"
            response["database_url"] = "Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "Connected"
    except Exception as e:
        response["database"] = f"Error: {str(e)[:50]}"
    response["database_url"] = "Set" if os.getenv("DATABASE_URL") else "Not Set"
    response["database_name"] = "Set" if os.getenv("DATABASE_NAME") else "Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
