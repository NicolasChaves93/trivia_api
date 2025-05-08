from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.usuario import Usuario
from app.services import participacion

async def get_usuarios(db: AsyncSession):
    result = await db.execute(select(Usuario))
    return result.scalars().all()

async def get_usuario_by_cedula(db: AsyncSession, cedula: str):
    """
    Obtiene un usuario por su número de cédula.

    Args:
        db (AsyncSession): Sesión de base de datos
        cedula (str): Número de cédula del usuario

    Returns:
        Optional[Usuario]: El usuario encontrado o None si no existe
    """
    result = await db.execute(select(Usuario).where(Usuario.cedula == cedula))
    return result.scalar_one_or_none()

async def create_usuario(db: AsyncSession, cedula: str, nombre: str):
    """
    Crea un nuevo usuario.

    Args:
        db (AsyncSession): Sesión de base de datos
        cedula (str): Número de cédula del usuario
        nombre (str): Nombre completo del usuario

    Returns:
        Usuario: El usuario creado

    Raises:
        IntegrityError: Si ya existe un usuario con la misma cédula
    """
    usuario = Usuario(cedula=cedula, nombre=nombre)
    try:
        db.add(usuario)
        await db.commit()
        await db.refresh(usuario)
        return usuario
    except Exception:
        await db.rollback()
        raise

async def delete_usuario_by_cedula(db: AsyncSession, cedula: str):
    """
    Elimina todas las participaciones asociadas a un usuario y luego elimina al usuario.

    Args:
        db (AsyncSession): Sesión de base de datos
        cedula (str): Número de cédula del usuario a eliminar

    Returns:
        Optional[Usuario]: El usuario eliminado o None si no existía
    """
    usuario = await get_usuario_by_cedula(db, cedula)
    if not usuario:
        return None

    # Eliminar participaciones primero (usando tu lógica existente)
    participaciones = await participacion.get_participaciones_por_usuario_evento(db, cedula=cedula)
    for p in participaciones:
        await participacion.eliminar_participacion(db, p.id_participacion)

    # Eliminar el usuario luego
    await db.delete(usuario)
    await db.commit()
    return usuario

async def delete_all_usuarios(db: AsyncSession):
    await db.execute(select(Usuario).delete())
    await db.commit()
