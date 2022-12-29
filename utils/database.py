import os
import uuid
from pathlib import Path
from typing import Any

import asyncpg
from exencolorlogs import FileLogger

from utils import env, paths


class Database:
    _pool: asyncpg.Pool

    def __init__(self) -> None:
        self._log: FileLogger = FileLogger("DB", folder=paths.LOGS)
        self._existence_ensurer = ExistenceEnsurer(self)

    @property
    def ex_es(self) -> "ExistenceEnsurer":
        return self._existence_ensurer

    async def connect(self) -> None:
        self._log.info("Connecting to database...")
        if env.db.DSN is not None:
            self._pool = await asyncpg.create_pool(env.db.DSN)
        else:
            self._pool = await asyncpg.create_pool(
                database=env.db.DATABASE, user=env.db.USER, password=env.db.PASSWORD, host=env.db.HOST, port=env.db.PORT
            )
        self._log.ok("Connected successfully")

        await self.__setup()
        await self.__check_migrations()

    async def close(self) -> None:
        self._log.info("Closing database connection...")
        await self._pool.close()
        self._log.ok("Connection was closed successfully")

    async def __setup(self) -> None:
        self._log.info("Executing setup scripts...")
        await self.execute(paths.SQL_CONFIG.read_text())
        self._log.ok("Setup was completed successfully")

    async def __check_migrations(self) -> None:
        script_first_executed: int = (await self.fetchval("SELECT script_executed FROM script_executed")).timestamp()
        files: list[str] = os.listdir(paths.MIGRATIONS)
        times = {}
        for name in files:
            if not name.endswith(".sql"):
                continue
            if (timestamp := int(name.split("-")[0])) < script_first_executed:
                continue

            times[name[:-4].split("-")[1]] = timestamp

        migrations = set(times.keys())
        applied_migrations: set[str] = set(r["id"].hex for r in await self.fetchall("SELECT id FROM migrations"))
        unapplied_migrations: set[str] = migrations - applied_migrations
        if len(unapplied_migrations) == 0:
            self._log.ok("All migrations are already applied!")
            return

        unapplied_migrations: list[str] = sorted(list(unapplied_migrations), key=times.get)
        self._log.warning("Found %s unapplied migrations, applying now...", len(unapplied_migrations))
        async with self._pool.acquire() as con:
            con: asyncpg.Connection
            async with con.transaction():
                for mig_id in unapplied_migrations:
                    path = paths.MIGRATIONS / Path(f"{times[mig_id]}-{mig_id}.sql")
                    try:
                        with open(path) as f:
                            await con.execute(f.read())
                            await con.execute("INSERT INTO migrations (id) VALUES ($1)", uuid.UUID(mig_id))
                            self._log.ok("Applied %s", mig_id)
                    except Exception as e:
                        self._log.critical("Failed to apply migration %s, all changes were reverted", mig_id)
                        raise e

        self._log.ok("All migrations were applied successfully!")

    async def execute(self, sql: str, *args: Any) -> None:
        await self._pool.execute(sql, *args)

    async def executemany(self, sql: str, *args: Any) -> None:
        await self._pool.executemany(sql, *args)

    async def fetchall(self, sql: str, *args: Any) -> list[asyncpg.Record]:
        data: list[asyncpg.Record] = await self._pool.fetch(sql, *args)
        return data

    async def fetchrow(self, sql: str, *args: Any) -> asyncpg.Record | None:
        return await self._pool.fetchrow(sql, *args)

    async def fetchval(self, sql: str, *args: Any) -> Any:
        return await self._pool.fetchval(sql, *args)


class ExistenceEnsurer:
    MAX_CACHE_SIZE: int = 1000

    def __init__(self, db: Database) -> None:
        self._db = db
        self._data: dict[str, list[Any]] = {}  # keys are table names, values are lists of key values

    async def _ensure_existence(self, table_name: str, key_field: str, key_value: Any) -> None:
        if table_name not in self._data:
            self._data[table_name] = []
        elif key_value in self._data[table_name]:
            return
        await self._db.execute(f"INSERT INTO {table_name} ({key_field}) VALUES ($1) ON CONFLICT DO NOTHING", key_value)
        self._add_entry(table_name, key_value)

    def _add_entry(self, table_name: str, key_value: Any):
        self._data[table_name].append(key_value)
        if len(self._data[table_name]) > self.MAX_CACHE_SIZE:
            self._data.clear()  # partial dict clear is expensive, so doing full
