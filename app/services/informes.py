from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

async def usuarios_pendientes(db: AsyncSession):
    query = text("""
        SELECT u.id_usuario, u.nombre, p.started_at
        FROM trivia.participaciones p
        JOIN trivia.usuarios u USING (id_usuario)
        WHERE p.estado = 'Pendiente'
    """)
    result = await db.execute(query)
    return result.fetchall()

async def usuarios_finalizados(db: AsyncSession):
    query = text("""
        SELECT u.id_usuario, u.nombre, p.finished_at
        FROM trivia.participaciones p
        JOIN trivia.usuarios u USING (id_usuario)
        WHERE p.estado = 'Finalizado'
    """)
    result = await db.execute(query)
    return result.fetchall()
