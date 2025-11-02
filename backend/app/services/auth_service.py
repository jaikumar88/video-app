"""
Authentication service for user management and JWT handling.
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.models.user import User, UserSession


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings = get_settings()

    async def get_user_by_email_or_phone(
        self, email: Optional[str] = None, phone_number: Optional[str] = None
    ) -> Optional[User]:
        """Get user by email or phone number."""
        if email:
            stmt = select(User).where(User.email == email)
        elif phone_number:
            stmt = select(User).where(User.phone_number == phone_number)
        else:
            return None

        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    def _generate_verification_code(self, length: int = 6) -> str:
        """Generate random verification code."""
        return "".join(secrets.choice(string.digits) for _ in range(length))

    def _generate_token(self, length: int = 32) -> str:
        """Generate random token."""
        return secrets.token_urlsafe(length)

    async def create_user(
        self,
        first_name: str,
        last_name: str,
        password: str,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> User:
        """Create a new user."""
        hashed_password = self._hash_password(password)

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number=phone_number,
            hashed_password=hashed_password,
            display_name=f"{first_name} {last_name}",
        )

        # Generate verification codes
        self.generate_verification_codes(user)

        try:
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("User with this email or phone already exists")

    def generate_verification_codes(self, user: User):
        """Generate and set verification codes for user."""
        if user.email:
            user.email_verification_token = self._generate_token()

        if user.phone_number:
            user.phone_verification_code = self._generate_verification_code()

        # Set expiration time (24 hours from now)
        user.verification_code_expires_at = datetime.utcnow() + timedelta(hours=24)

    async def authenticate_user(
        self, email_or_phone: str, password: str
    ) -> Optional[User]:
        """Authenticate user with email/phone and password."""
        # Determine if it's email or phone
        if "@" in email_or_phone:
            user = await self.get_user_by_email_or_phone(email=email_or_phone)
        else:
            user = await self.get_user_by_email_or_phone(phone_number=email_or_phone)

        if not user:
            return None

        if not self._verify_password(password, user.hashed_password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
            await self.db.commit()
            return None

        # Check if account is locked
        if user.account_locked_until and user.account_locked_until > datetime.utcnow():
            return None

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.account_locked_until = None
        await self.db.commit()

        return user

    async def verify_email(self, verification_token: str) -> bool:
        """Verify user's email with verification token."""
        stmt = select(User).where(
            User.email_verification_token == verification_token,
            User.verification_code_expires_at > datetime.utcnow(),
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.email_verified = True
        user.email_verification_token = None
        await self.db.commit()
        return True

    async def verify_phone(self, verification_code: str) -> bool:
        """Verify user's phone with verification code."""
        stmt = select(User).where(
            User.phone_verification_code == verification_code,
            User.verification_code_expires_at > datetime.utcnow(),
        )
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return False

        user.phone_verified = True
        user.phone_verification_code = None
        await self.db.commit()
        return True

    def _create_jwt_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT token."""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire})

        return jwt.encode(
            to_encode, self.settings.SECRET_KEY, algorithm=self.settings.JWT_ALGORITHM
        )

    async def create_access_token(self, user_id: UUID) -> str:
        """Create access token for user."""
        data = {"sub": str(user_id), "type": "access"}
        return self._create_jwt_token(
            data, timedelta(minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

    async def create_refresh_token(self, user_id: UUID) -> str:
        """Create refresh token for user."""
        data = {"sub": str(user_id), "type": "refresh"}

        refresh_token = self._create_jwt_token(
            data, timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        # Store session in database
        session = UserSession(
            user_id=user_id,
            session_token=self._generate_token(),
            refresh_token=refresh_token,
            expires_at=datetime.utcnow()
            + timedelta(days=self.settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        self.db.add(session)
        await self.db.commit()

        return refresh_token

    async def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from access token."""
        try:
            payload = jwt.decode(
                token,
                self.settings.SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM],
            )

            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "access":
                return None

            return await self.get_user_by_id(UUID(user_id))

        except JWTError:
            return None

    async def refresh_tokens(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access and refresh tokens."""
        try:
            payload = jwt.decode(
                refresh_token,
                self.settings.SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM],
            )

            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "refresh":
                return None

            # Verify refresh token exists in database
            stmt = select(UserSession).where(
                UserSession.user_id == UUID(user_id),
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow(),
            )
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()

            if not session:
                return None

            # Create new tokens
            new_access_token = await self.create_access_token(UUID(user_id))
            new_refresh_token = await self.create_refresh_token(UUID(user_id))

            # Revoke old refresh token
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            await self.db.commit()

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
            }

        except JWTError:
            return None

    async def logout_user(self, token: str):
        """Logout user and revoke all sessions."""
        try:
            payload = jwt.decode(
                token,
                self.settings.SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM],
            )

            user_id: str = payload.get("sub")
            if user_id:
                # Revoke all active sessions
                stmt = (
                    update(UserSession)
                    .where(
                        UserSession.user_id == UUID(user_id),
                        UserSession.is_active == True,
                    )
                    .values(is_active=False, revoked_at=datetime.utcnow())
                )
                await self.db.execute(stmt)
                await self.db.commit()

        except JWTError:
            pass  # Invalid token, nothing to revoke

    async def update_last_login(self, user_id: UUID):
        """Update user's last login timestamp."""
        stmt = (
            update(User).where(User.id == user_id).values(last_login=datetime.utcnow())
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def create_admin_user_if_not_exists(self):
        """Create default admin user if no admin exists."""
        # Check if any admin user exists
        stmt = select(User).where(User.is_superuser.is_(True))
        result = await self.db.execute(stmt)
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            # Ensure the default admin account stays accessible
            updated = False

            if not existing_admin.is_active:
                existing_admin.is_active = True
                updated = True

            if existing_admin.failed_login_attempts:
                existing_admin.failed_login_attempts = 0
                updated = True

            if existing_admin.account_locked_until is not None:
                existing_admin.account_locked_until = None
                updated = True

            if not existing_admin.email_verified:
                existing_admin.email_verified = True
                updated = True

            if existing_admin.email is None:
                existing_admin.email = "admin@videoapp.com"
                updated = True

            if updated:
                await self.db.commit()
                await self.db.refresh(existing_admin)

            return existing_admin
        
        # Create default admin user
        admin_user = User(
            first_name="Admin",
            last_name="User",
            email="admin@videoapp.com",
            hashed_password=self._hash_password("admin"),
            display_name="Admin User",
            is_superuser=True,
            email_verified=True,  # Auto-verify admin
            is_active=True
        )
        
        try:
            self.db.add(admin_user)
            await self.db.commit()
            await self.db.refresh(admin_user)
            return admin_user
        except IntegrityError:
            await self.db.rollback()
            # If there's a conflict, try to get existing user
            stmt = select(User).where(User.email == "admin@videoapp.com")
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
