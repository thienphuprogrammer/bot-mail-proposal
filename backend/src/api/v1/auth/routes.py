from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# from src.core.auth import create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# # Password hashing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # Models
# class Token(BaseModel):
#     access_token: str
#     token_type: str

# class TokenData(BaseModel):
#     username: str | None = None

# class User(BaseModel):
#     username: str
#     email: str | None = None
#     full_name: str | None = None
#     disabled: bool | None = None

# class UserInDB(User):
#     hashed_password: str

# @router.post("/token", response_model=Token)
# async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
#     """
#     Get access token for authentication.
#     """
#     try:
#         # Verify credentials (implement your user verification logic here)
#         user = verify_user(form_data.username, form_data.password)
#         if not user:
#             raise HTTPException(
#                 status_code=401,
#                 detail="Incorrect username or password",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )

#         # Create access token
#         access_token = create_access_token(
#             data={"sub": user.username}
#         )
#         return {"access_token": access_token, "token_type": "bearer"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/me", response_model=User)
# async def read_users_me(current_user: Dict = Depends(get_current_user)):
#     """
#     Get current user information.
#     """
#     try:
#         return current_user
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/register")
# async def register_user(
#     username: str = Query(..., description="Username for the new account"),
#     email: str = Query(..., description="Email address for the new account"),
#     password: str = Query(..., description="Password for the new account"),
#     full_name: str = Query(None, description="Full name of the user")
# ):
#     """
#     Register a new user.
#     """
#     try:
#         # Check if user already exists
#         if user_exists(username):
#             raise HTTPException(status_code=400, detail="Username already registered")

#         # Create new user
#         hashed_password = pwd_context.hash(password)
#         user = UserInDB(
#             username=username,
#             email=email,
#             full_name=full_name,
#             hashed_password=hashed_password,
#             disabled=False
#         )

#         # Save user to database (implement your user storage logic here)
#         save_user(user)

#         return {"message": "User registered successfully"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# # Helper functions (implement these based on your user management system)
# def verify_user(username: str, password: str) -> UserInDB | None:
#     """
#     Verify user credentials.
#     """
#     # Implement your user verification logic here
#     pass

# def user_exists(username: str) -> bool:
#     """
#     Check if a user exists.
#     """
#     # Implement your user existence check logic here
#     pass

# def save_user(user: UserInDB):
#     """
#     Save a new user to the database.
#     """
#     # Implement your user storage logic here
#     pass
