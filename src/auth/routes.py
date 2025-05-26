from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, status, BackgroundTasks
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import Config
from src.db.main import get_session
from src.db.redis_client import add_jti_to_blocklist
from src.errors import InvalidCredentials, InvalidToken, UserAlreadyExists, UserNotFound
from src.mail import create_message, mail

from .dependencies import (
    AccessTokenBearer,
    RefreshTokenBearer,
    RoleChecker,
    get_current_user,
)
from .schemas import (
    EmailModel,
    PasswordResetConfirmModel,
    PasswordResetRequestModel,
    UserBooksModel,
    UserCreateModel,
    UserLoginModel,
)
from .service import UserService
from .utils import (
    create_access_token,
    create_url_safe_token,
    decode_url_safe_token,
    generate_pass_hash,
    verify_password,
)

from src.celery_tasks import send_email_celery

auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(["admin", "user"])

REFRESH_TOKEN_EXPIRY = 2


@auth_router.post("/send-email")
async def send_email(emails: EmailModel):
    emails = emails.adressess

    subject = "Welcome email."

    html = "<h1>ПРИВІТТТТТ</h1>"

    send_email_celery.delay(emails, subject, html)

    return {"message": "Send successfully."}


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_Account(
    user_data: UserCreateModel,
    bg_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    Create user account using email, username, first_name, last_name
    params:
        user_data: UserCreateModel
    """
    email = user_data.email

    user_exists = await user_service.user_exists(email, session)

    if user_exists:
        raise UserAlreadyExists()

    new_user = await user_service.create_user(user_data, session)

    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"

    html = f"""
    <h1>Verify your Email</h1>
    <p>Please click this <a href="{link}">link</a> to verify your email</p>
    """

    emails = [email]

    subject = "Verify Your email"

    send_email_celery.delay(emails, subject, html)

    return {
        "message": "Account Created! Check email to verify your account",
        "user": new_user,
    }

@auth_router.get("/verify/{token}")
async def verify_user_account(token: str, session: AsyncSession = Depends(get_session)):
    token_data = decode_url_safe_token(token)

    user_email = token_data.get("email")
    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise UserNotFound()

        await user_service.update_user(user, {"is_verified": True}, session)

        return JSONResponse(
            content={"message": "Account Veryfied."}, status_code=status.HTTP_200_OK
        )

    return JSONResponse(
        content={"message": "Error during verification."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@auth_router.post("/login")
async def login_users(
    login_data: UserLoginModel, session: AsyncSession = Depends(get_session)
) -> dict:
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email, session)

    if user is not None:
        password_valid = verify_password(password, user.password_hash)

        if password_valid:
            access_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid),
                    "role": user.role,
                }
            )

            refresh_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid),
                },
                refresh=True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
            )

            return JSONResponse(
                content={
                    "message": "Loggin successful.",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {"email": user.email, "uid": str(user.uid)},
                }
            )
    raise InvalidCredentials()


@auth_router.get("/refresh-token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(user_data=token_details["user"])
        return JSONResponse(
            content={
                "refresh_token": new_access_token,
            }
        )

    raise InvalidToken()


@auth_router.get("/logout")
async def revooke_token(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details["jti"]
    await add_jti_to_blocklist(jti)
    return JSONResponse(
        content={"message": "Logged out successfuly."},
        status_code=status.HTTP_200_OK,
    )


@auth_router.get("/me", response_model=UserBooksModel)
async def get_current_user(
    user=Depends(get_current_user),
    _: bool = Depends(role_checker),
):
    return user


@auth_router.post("/password-reset")
async def password_reset(email_data: PasswordResetRequestModel):
    email = email_data.email

    token = create_url_safe_token({"email": email})

    link = f"http://{Config.DOMAIN}/api/v1/auth/password-reset-confirm/{token}"

    html_message = f"""
        Reset password, click link: {link}
    """

    message = create_message(
        recipients=[email], subject="Reset password.", body=html_message
    )

    await mail.send_message(message)

    return JSONResponse(
        content={"message": "Check your email and follow instructions."},
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/password-reset-confirm/{token}")
async def reset_password(
    token: str,
    passwords: PasswordResetConfirmModel,
    session: AsyncSession = Depends(get_session),
):
    new_password = passwords.new_password
    confirmed_password = passwords.confirm_new_password

    if new_password != confirmed_password:
        raise HTTPException(
            detail="Passwords not match", status_code=status.HTTP_400_BAD_REQUEST
        )

    token_data = decode_url_safe_token(token)

    user_email = token_data.get("email")
    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise UserNotFound()

        password_hash = generate_pass_hash(new_password)

        await user_service.update_user(user, {"password_hash": password_hash}, session)

        return JSONResponse(
            content={"message": "Password reset successfully."},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"message": "Error during password reset."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
