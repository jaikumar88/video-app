"""
Admin API endpoints for user management.
Requires admin authentication.
"""

from datetime import datetime
from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.api.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic models
class UserListResponse(BaseModel):
    id: str
    email: Optional[str]
    phone_number: Optional[str]
    first_name: str
    last_name: str
    display_name: Optional[str]
    email_verified: bool
    phone_verified: bool
    is_active: bool
    is_superuser: bool
    created_at: datetime
    last_login: Optional[datetime]


class UserUpdateRequest(BaseModel):
    email_verified: Optional[bool] = None
    phone_verified: Optional[bool] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class AdminStatsResponse(BaseModel):
    total_users: int
    verified_users: int
    unverified_users: int
    active_users: int
    inactive_users: int
    admin_users: int


# Dependency to check if user is admin
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify that the current user is an admin."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Get platform statistics for admin dashboard."""
    logger.info(f"🔧 Admin {admin_user.email} requested platform statistics")
    
    # Get user counts
    total_users_result = await db.execute(select(User).where(User.id.isnot(None)))
    total_users = len(total_users_result.scalars().all())
    
    verified_users_result = await db.execute(
        select(User).where((User.email_verified == True) | (User.phone_verified == True))
    )
    verified_users = len(verified_users_result.scalars().all())
    
    active_users_result = await db.execute(select(User).where(User.is_active == True))
    active_users = len(active_users_result.scalars().all())
    
    admin_users_result = await db.execute(select(User).where(User.is_superuser == True))
    admin_users = len(admin_users_result.scalars().all())
    
    return AdminStatsResponse(
        total_users=total_users,
        verified_users=verified_users,
        unverified_users=total_users - verified_users,
        active_users=active_users,
        inactive_users=total_users - active_users,
        admin_users=admin_users
    )


@router.get("/users", response_model=List[UserListResponse])
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    verified_only: Optional[bool] = Query(None, description="Filter by verification status"),
    active_only: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Get paginated list of users with optional filtering."""
    logger.info(f"🔧 Admin {admin_user.email} requested user list")
    
    # Build query
    query = select(User)
    
    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_pattern)) |
            (User.first_name.ilike(search_pattern)) |
            (User.last_name.ilike(search_pattern))
        )
    
    if verified_only is not None:
        if verified_only:
            query = query.where((User.email_verified == True) | (User.phone_verified == True))
        else:
            query = query.where((User.email_verified == False) & (User.phone_verified == False))
    
    if active_only is not None:
        query = query.where(User.is_active == active_only)
    
    # Add ordering and pagination
    query = query.order_by(desc(User.created_at))
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [
        UserListResponse(
            id=str(user.id),
            email=user.email,
            phone_number=user.phone_number,
            first_name=user.first_name,
            last_name=user.last_name,
            display_name=user.display_name,
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
            last_login=user.last_login
        )
        for user in users
    ]


@router.get("/users/{user_id}", response_model=UserListResponse)
async def get_user_details(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Get detailed information about a specific user."""
    logger.info(f"🔧 Admin {admin_user.email} requested details for user {user_id}")
    
    # Get user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserListResponse(
        id=str(user.id),
        email=user.email,
        phone_number=user.phone_number,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.patch("/users/{user_id}", response_model=UserListResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Update user status (verify, activate/deactivate, make admin)."""
    logger.info(f"🔧 Admin {admin_user.email} updating user {user_id}")
    
    # Get user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deactivating themselves
    if str(user.id) == str(admin_user.id) and user_update.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    # Update fields
    update_data = {}
    if user_update.email_verified is not None:
        update_data["email_verified"] = user_update.email_verified
        logger.info(f"📧 Setting email_verified to {user_update.email_verified}")
    
    if user_update.phone_verified is not None:
        update_data["phone_verified"] = user_update.phone_verified
        logger.info(f"📱 Setting phone_verified to {user_update.phone_verified}")
    
    if user_update.is_active is not None:
        update_data["is_active"] = user_update.is_active
        logger.info(f"👤 Setting is_active to {user_update.is_active}")
    
    if user_update.is_superuser is not None:
        update_data["is_superuser"] = user_update.is_superuser
        logger.info(f"🔧 Setting is_superuser to {user_update.is_superuser}")
    
    # Apply updates
    if update_data:
        stmt = update(User).where(User.id == user_id).values(**update_data)
        await db.execute(stmt)
        await db.commit()
        
        # Refresh user data
        await db.refresh(user)
    
    return UserListResponse(
        id=str(user.id),
        email=user.email,
        phone_number=user.phone_number,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        last_login=user.last_login
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Delete a user from the platform."""
    logger.info(f"🔧 Admin {admin_user.email} deleting user {user_id}")
    
    # Prevent admin from deleting themselves
    if str(user_id) == str(admin_user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Check if user exists
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user
    stmt = delete(User).where(User.id == user_id)
    await db.execute(stmt)
    await db.commit()
    
    logger.info(f"🗑️ User {user.email or user.phone_number} deleted successfully")
    
    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/verify-email")
async def admin_verify_email(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Manually verify a user's email (admin override)."""
    logger.info(f"🔧 Admin {admin_user.email} manually verifying email for user {user_id}")
    
    stmt = update(User).where(User.id == user_id).values(
        email_verified=True,
        email_verification_token=None
    )
    result = await db.execute(stmt)
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.commit()
    return {"message": "Email verified successfully"}


@router.post("/users/{user_id}/verify-phone")
async def admin_verify_phone(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Manually verify a user's phone (admin override)."""
    logger.info(f"🔧 Admin {admin_user.email} manually verifying phone for user {user_id}")
    
    stmt = update(User).where(User.id == user_id).values(
        phone_verified=True,
        phone_verification_code=None
    )
    result = await db.execute(stmt)
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.commit()
    return {"message": "Phone verified successfully"}