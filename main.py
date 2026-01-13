
  import os
  import requests
  from fastapi import FastAPI, HTTPException
  from fastapi.middleware.cors import CORSMiddleware
  from pydantic import BaseModel
  from typing import List

  from database import db, create_document, get_documents
  from schemas import Booking

  # Airtable configuration
  AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
  AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "appGjTxtqqtnevO6x")
  AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "UNTZ UNTZ Investor CRM")

  def send_to_airtable(booking_data: dict):
      """Send booking data to Airtable"""
      if not AIRTABLE_API_KEY:
          print("Warning: AIRTABLE_API_KEY not set, skipping Airtable")
          return None

      url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
      headers = {
          "Authorization": f"Bearer {AIRTABLE_API_KEY}",
          "Content-Type": "application/json"
      }

      # Map booking fields to Airtable columns
      airtable_record = {
          "fields": {
              "Name": booking_data.get("name", ""),
              "Full Name": booking_data.get("full_name", ""),
              "Email": booking_data.get("email", ""),
              "Company Website": booking_data.get("company_website", ""),
              "Services": booking_data.get("services", ""),
              "Timeline": booking_data.get("timeline", ""),
              "Challenge": booking_data.get("challenge", ""),
              "Budget": booking_data.get("budget", ""),
              "Language": booking_data.get("language", "en")
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
      """
      Create a booking/consultation request.
      Stores in MongoDB collection "booking" and sends to Airtable.
      """
      if db is None:
          raise HTTPException(status_code=500, detail="Database not available")
      try:
          inserted_id = create_document("booking", booking)

          # Also send to Airtable
          booking_dict = booking.model_dump()
          send_to_airtable(booking_dict)

          return {"status": "ok", "id": inserted_id}
      except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

  @app.get("/api/bookings", response_model=List[dict])
  def list_bookings(limit: int = 50):
      """
      List recent booking/consultation requests.
      """
      if db is None:
          raise HTTPException(status_code=500, detail="Database not available")
      try:
          docs = get_documents("booking", {}, limit)
          # Convert ObjectId to string
          for d in docs:
              if "_id" in d:
                  d["_id"] = str(d["_id"])
          return docs
      except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

  @app.get("/test")
  def test_database():
      """Test endpoint to check if database is available and accessible"""
      response = {
          "backend": "✅ Running",
          "database": "❌ Not Available",
          "database_url": None,
          "database_name": None,
          "connection_status": "Not Connected",
          "collections": []
      }

      try:
          if db is not None:
              response["database"] = "✅ Available"
              response["database_url"] = "✅ Configured"
              response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
              response["connection_status"] = "Connected"
              try:
                  collections = db.list_collection_names()
                  response["collections"] = collections[:10]
                  response["database"] = "✅ Connected & Working"
              except Exception as e:
                  response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
          else:
              response["database"] = "⚠️  Available but not initialized"

      except Exception as e:
          response["database"] = f"❌ Error: {str(e)[:50]}"

      response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
      response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

      return response


  if __name__ == "__main__":
      import uvicorn
      port = int(os.getenv("PORT", 8000))
      uvicorn.run(app, host="0.0.0.0", port=port)
