from models import User  # Assuming User is defined in the models script
from slowapi import Limiter
from slowapi.util import get_remote_address
from typing import Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from geoalchemy2.elements import WKTElement
import httpx
from fastapi import HTTPException
from sqlalchemy.sql import text
from pydantic import BaseModel

limiter = Limiter(key_func=get_remote_address)


async def real_geolocate(address: str) -> Tuple[float, float]:
    """
    Convert an address to latitude and longitude using the OpenStreetMap Nominatim API asynchronously.

    Args:
        address (str): The address to geolocate.

    Returns:
        A tuple containing the latitude and longitude.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1,  # We only want the top result
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        if not data:
            raise ValueError(f"No geolocation data found for address: {address}")

        latitude = float(data[0]["lat"])
        longitude = float(data[0]["lon"])

        return (latitude, longitude)


async def encode_user_location(db: AsyncSession, username: str, address: str) -> None:
    try:
        # Attempt to geolocate the address
        lat, lon = await real_geolocate(address)
    except ValueError as ve:
        # Handle specific errors from real_geolocate, e.g., no data found
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        # Handle unexpected errors from geolocation
        raise HTTPException(status_code=500, detail=f"Geolocation error: {str(e)}")

    try:
        # Execute the update query within a transaction
        query = text(
            "UPDATE users SET location = ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) WHERE username = :username"
        )
        await db.execute(query, {"lat": lat, "lon": lon, "username": username})
        await db.commit()
    except Exception as e:
        # Handle any database-related errors
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database update error: {str(e)}")





class Location(BaseModel):
    latitude: float
    longitude: float


async def update_user_location(
    db: AsyncSession, username: str, location: Location
) -> None:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update the user's location using WKTElement to create a POINT
    user.location = WKTElement(f"POINT({location.longitude} {location.latitude})")
    db.add(user)
    await db.commit()


async def get_user(db: AsyncSession, username: str) -> User:
    # Asynchronously retrieve a user by their username
    async for user in db.execute(
        "SELECT * FROM users WHERE username = :username", {"username": username}
    ):
        return user.first()
