import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(user='activia', password='activia', database='activia_trace', host='postgres')
    for t in ['carrera','cohorte','materia']:
        r = await conn.fetchval("select to_regclass('public.' || $1)", t)
        print(t, r)
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
