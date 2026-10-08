from pydantic import BaseModel, ConfigDict, EmailStr, Field


CLIENT_TYPES = (
    "household",
    "restaurant",
    "hospital",
    "factory",
    "shop",
    "school",
    "office",
    "hotel",
    "market",
    "other",
)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    client_type: str | None = Field(default=None, max_length=40)
    default_address: str | None = Field(default=None, max_length=500)
    default_latitude: float | None = Field(default=None, ge=-90, le=90)
    default_longitude: float | None = Field(default=None, ge=-180, le=180)


class ResidentProfileUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    client_type: str = Field(max_length=40)
    default_address: str = Field(min_length=5, max_length=500)
    default_latitude: float = Field(ge=-90, le=90)
    default_longitude: float = Field(ge=-180, le=180)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: str
    client_type: str | None
    default_address: str | None
    default_latitude: float | None
    default_longitude: float | None
    collection_weekday: int
    is_active: bool
