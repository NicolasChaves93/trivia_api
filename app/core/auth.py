from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.settings_instance import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/loginU")  # importante para Swagger


def crear_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc)+ timedelta(minutes = settings.jwt_expiration_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm = settings.jwt_algorithm)

def verificar_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


ADMIN_ROLES = {"admin", "superadmin"}


def require_admin(token: str = Depends(oauth2_scheme)) -> dict:
    """Exige un access token de administración emitido por auth_api (RS256).

    Se valida la firma con la clave PÚBLICA de auth_api (esta API no emite estos
    tokens, solo los valida) y que el claim de rol sea admin/superadmin.
    Es independiente de `verificar_token`, que valida tokens de participante (HS256).
    """
    pem = settings.admin_public_key_pem
    if not pem:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Validación de administración no configurada (falta clave pública)",
        )
    try:
        payload = jwt.decode(token, pem, algorithms=[settings.admin_jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de administración inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    if payload.get("type") not in (None, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Se requiere un access token"
        )
    if payload.get("rol") not in ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere privilegios de administrador",
        )
    return payload