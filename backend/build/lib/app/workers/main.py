"""RESERVADO para ADR-003: entrypoint del worker de background.

C-01 establece solo un loop no-op como placeholder.
La tecnología real de la cola (ARQ, Celery, asyncio propio) se define cuando
se construye el módulo de comunicaciones.
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Worker started (placeholder — no-op loop)")
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
