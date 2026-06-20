import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.database import create_engine, create_session_factory
from app.models.comunicacion import Comunicacion, EstadoComunicacion
from app.repositories.comunicacion_repository import ComunicacionRepository
from app.services.comunicacion_service import ComunicacionService

logger = logging.getLogger(__name__)


class ComunicacionWorker:
    def __init__(
        self,
        settings: Settings | None = None,
    ) -> None:
        self._settings = settings or Settings()
        self._interval = self._settings.worker_poll_interval_seconds
        self._batch_size = self._settings.worker_batch_size
        self._service = ComunicacionService()
        self._repo = ComunicacionRepository()
        self._engine = create_engine(self._settings)
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._running = False

    async def _get_session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._session_factory = create_session_factory(self._engine)
        return self._session_factory

    async def _process_pendientes_sin_aprobacion(self) -> int:
        factory = await self._get_session_factory()
        session = factory()
        processed = 0
        try:
            tenant_ids = await self._get_active_tenant_ids(session)
            for tenant_id in tenant_ids:
                pendientes = await self._repo.list_pendientes_para_worker(
                    tenant_id=tenant_id,
                    limit=self._batch_size,
                    session=session,
                )
                for comunicacion in pendientes:
                    await self._procesar_comunicacion(comunicacion, session)
                    processed += 1
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Error in _process_pendientes_sin_aprobacion")
        finally:
            await session.close()
        return processed

    async def _process_enviando(self) -> int:
        factory = await self._get_session_factory()
        session = factory()
        processed = 0
        try:
            tenant_ids = await self._get_active_tenant_ids(session)
            for tenant_id in tenant_ids:
                enviando = await self._repo.list_by_estado(
                    tenant_id=tenant_id,
                    estado=EstadoComunicacion.Enviando,
                    session=session,
                )
                for comunicacion in enviando:
                    await self._procesar_comunicacion(comunicacion, session)
                    processed += 1
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Error in _process_enviando")
        finally:
            await session.close()
        return processed

    async def _procesar_comunicacion(
        self,
        comunicacion: Comunicacion,
        session: AsyncSession,
    ) -> None:
        comunicacion.estado = EstadoComunicacion.Enviando.value
        await session.flush()

        destinatario = ComunicacionService._descifrar_destinatario(comunicacion.destinatario)
        exito = await ComunicacionService._enviar_email(
            destinatario=destinatario,
            asunto=comunicacion.asunto,
            cuerpo=comunicacion.cuerpo,
        )

        if exito:
            comunicacion.estado = EstadoComunicacion.Enviado.value
            from datetime import datetime, timezone
            comunicacion.enviado_at = datetime.now(timezone.utc)
        else:
            comunicacion.estado = EstadoComunicacion.Error.value

    async def _get_active_tenant_ids(self, session: AsyncSession) -> list:
        from app.models.tenant import Tenant
        stmt = select(Tenant.id).where(Tenant.activo.is_(True))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def run_once(self) -> tuple[int, int]:
        p1 = await self._process_pendientes_sin_aprobacion()
        p2 = await self._process_enviando()
        return p1, p2

    async def run_forever(self) -> None:
        self._running = True
        logger.info(
            "ComunicacionWorker started (interval=%ds, batch_size=%d)",
            self._interval,
            self._batch_size,
        )
        try:
            while self._running:
                pendientes, enviando = await self.run_once()
                if pendientes or enviando:
                    logger.info("Worker: %d pendientes, %d enviando processed", pendientes, enviando)
                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            logger.info("ComunicacionWorker stopped")
        finally:
            await self._engine.dispose()

    def stop(self) -> None:
        self._running = False
