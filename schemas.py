"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field, EmailStr, AnyHttpUrl
from typing import Optional, Literal

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Add your own schemas here:
# --------------------------------------------------

class Booking(BaseModel):
    """
    Booking requests for diagnostic/consultation calls
    Collection name: "booking"
    """
    # Contact details
    name: str = Field(..., min_length=2, description="Contact name")
    full_name: Optional[str] = Field(None, min_length=2, description="Full legal name")
    email: EmailStr = Field(..., description="Work email")
    company: str = Field(..., min_length=1, description="Company name")
    company_website: Optional[AnyHttpUrl] = Field(None, description="Company website URL")
    phone: Optional[str] = Field(None, min_length=5, description="Phone number")

    # Project details
    services: Optional[str] = Field(None, description="Services of interest")
    timeline: Optional[Literal['<30_days','<3_months','<12_months']] = Field(None, description="Desired project timeline")
    challenge: Optional[str] = Field(None, description="Primary business challenge")
    budget: Optional[Literal['under_2500','2500_10000','undetermined']] = Field(None, description="Estimated budget bracket")

    # Localization
    language: Optional[str] = Field(None, description="Language code (en|fr|nl)")
