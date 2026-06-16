from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.settings_instance import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/loginU")  # importante para Swagger

# Rol requerido para operaciones de administración. El token lo emite la API de
# autenticación (servicio aparte); esta API solo valida el JWT y el rol.
ADMIN_ROLE = "admin"

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


def require_admin(payload: dict = Depends(verificar_token)) -> dict:
    """Exige un JWT válido con rol de administración.

    El token lo emite la API de autenticación (servicio independiente) y se firma
    con el `SECRET_KEY` compartido. Aquí solo se valida la firma (vía
    `verificar_token`) y que el claim de rol sea de administrador.

    Soporta tanto un claim `rol`/`role` simple como una lista `roles`.
    """
    rol = payload.get("rol") or payload.get("role")
    roles = payload.get("roles") or ([rol] if rol else [])
    if ADMIN_ROLE not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere privilegios de administrador",
        )
    return payload