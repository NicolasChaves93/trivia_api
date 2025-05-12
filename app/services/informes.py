from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, desc, asc
from sqlalchemy.future import select
from app.schemas.informes import RankingUsuarioOut
from app.models import Usuario, Participacion, Resultado, Grupo

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

async def ranking_usuarios(
    db: AsyncSession,
    grupo_id: int = None,
    numero_intento: int = None
) -> list[RankingUsuarioOut]:
    stmt = (
        select(
            Usuario.cedula,
            Usuario.nombre,
            Grupo.nombre_grupo,
            Resultado.tiempo_total,
            Resultado.total_preguntas,
            Resultado.respuestas_correctas,
        )
        .join(Participacion, Usuario.id_usuario == Participacion.id_usuario)
        .join(Resultado, Participacion.id_participacion == Resultado.id_participacion)
        .join(Grupo, Participacion.id_grupo == Grupo.id_grupo)
        .where(
            (Participacion.id_grupo == grupo_id if grupo_id is not None else True),
            (Participacion.numero_intento == numero_intento if numero_intento is not None else True)
        )
        .order_by(
            desc(Resultado.respuestas_correctas),
            asc(Resultado.tiempo_total)
        )
    )

    result = await db.execute(stmt)
    rows = result.all()

    return [
        RankingUsuarioOut(
            ranking              = idx + 1,
            cedula               = row[0],
            nombre               = row[1],
            grupo                = str(row[2]),
            tiempo_juego         = str(row[3]),
            total_preguntas      = row[4],
            respuestas_correctas = row[5],
        )
        for idx, row in enumerate(rows)
    ]