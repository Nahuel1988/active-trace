import asyncio
import logging

from app.workers.comunicacion_worker import ComunicacionWorker

logger = logging.getLogger(__name__)


async def main() -> None:
    worker = ComunicacionWorker()
    await worker.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
