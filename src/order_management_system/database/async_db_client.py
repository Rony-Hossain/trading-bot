from __future__ import annotations

import logging
import aiosqlite
import json
from datetime import datetime
from typing import Callable, List, Optional, TypeVar, Any

from base_interfaces.db_interface import DatabaseInterface, DatabaseSession
from src.order_management_system.base_types.ids_and_enums import AccountId, OMSId, Symbol
from .db_types import OrderRow, FillRow, PositionRow, AccountSnapshotRow, EventLogRow

log = logging.getLogger(__name__)

T = TypeVar("T")

class SqliteSession(DatabaseSession):
    """
    A concrete session wrapper for aiosqlite.Connection.
    """
    def __init__(self, connection: aiosqlite.Connection):
        self.conn = connection

    async def commit(self):
        await self.conn.commit()

    async def rollback(self):
        await self.conn.rollback()

class AsyncDbClient(DatabaseInterface):
    """
    Concrete SQLite implementation of DatabaseInterface.
    """

    def __init__(self, db_path: str = "oms.db"):
        self.db_path = db_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def init_db(self):
        """
        Initialize the database tables. Call this on startup.
        """
        self._conn = await aiosqlite.connect(self.db_path)
        # Enable WAL mode for better concurrency
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._create_tables()
        log.info(f"Database initialized at {self.db_path}")

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def _create_tables(self):
        # ORDER TABLE
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                oms_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT,
                symbol TEXT,
                side TEXT,
                qty REAL,
                order_type TEXT,
                time_in_force TEXT,
                status TEXT,
                broker_order_id TEXT,
                perm_id INTEGER,
                limit_price REAL,
                stop_price REAL,
                filled_qty REAL DEFAULT 0.0,
                avg_fill_price REAL DEFAULT 0.0,
                last_fill_price REAL,
                created_at TIMESTAMP,
                last_update TIMESTAMP,
                meta TEXT
            )
        """)
        # FILLS TABLE
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS fills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oms_id INTEGER,
                execution_id TEXT UNIQUE,
                symbol TEXT,
                qty REAL,
                price REAL,
                commission REAL,
                fill_time TIMESTAMP,
                meta TEXT
            )
        """)
        # POSITIONS TABLE
        await self._conn.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                account_id TEXT,
                symbol TEXT,
                qty REAL,
                avg_price REAL,
                realized_pnl_today REAL,
                unrealized_pnl REAL,
                last_update TIMESTAMP,
                meta TEXT,
                PRIMARY KEY (account_id, symbol)
            )
        """)
        await self._conn.commit()

    # ------------------------------------------------------------------
    # Transaction Management
    # ------------------------------------------------------------------

    async def run_in_transaction(self, fn: Callable[[DatabaseSession], T]) -> T:
        """
        Wraps a function in a SQLite transaction.
        """
        if not self._conn:
            raise RuntimeError("Database not initialized. Call init_db() first.")
        
        # aiosqlite manages transactions via context manager usually, but we need
        # to expose the session to the callback.
        async with self._conn.cursor() as cursor:
            # Note: explicit BEGIN is handled by aiosqlite on execute, 
            # but we'll rely on commit/rollback in the session or auto-commit behavior
            session = SqliteSession(self._conn)
            try:
                result = await fn(session)
                await self._conn.commit()
                return result
            except Exception as e:
                await self._conn.rollback()
                raise e

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    async def get_order(self, oms_id: OMSId) -> Optional[OrderRow]:
        if not self._conn: return None
        async with self._conn.execute("SELECT * FROM orders WHERE oms_id = ?", (oms_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._map_row_to_order(row, cursor.description)
        return None

    async def insert_order(self, session: DatabaseSession, row: OrderRow) -> None:
        assert isinstance(session, SqliteSession)
        
        # Convert meta dict to JSON string
        meta_json = json.dumps(row.meta)
        
        # Determine oms_id: if 0 or None, let DB assign (but OrderRow expects strict int).
        # In a real scenario, you might reserve IDs. Here we let SQLite autoincrement.
        
        query = """
            INSERT INTO orders (
                account_id, symbol, side, qty, order_type, time_in_force, 
                status, broker_order_id, perm_id, limit_price, stop_price, 
                filled_qty, avg_fill_price, created_at, last_update, meta
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            row.account_id, row.symbol, row.side, row.qty, row.order_type, row.time_in_force,
            row.status, row.broker_order_id, row.perm_id, row.limit_price, row.stop_price,
            row.filled_qty, row.avg_fill_price, row.created_at, row.last_update, meta_json
        )
        
        cursor = await session.conn.execute(query, params)
        # We need to update the row's oms_id with the one generated by SQLite
        row.oms_id = cursor.lastrowid # type: ignore

    async def update_order(self, session: DatabaseSession, row: OrderRow) -> None:
        assert isinstance(session, SqliteSession)
        meta_json = json.dumps(row.meta)
        
        query = """
            UPDATE orders SET 
                status=?, broker_order_id=?, perm_id=?, filled_qty=?, 
                avg_fill_price=?, last_fill_price=?, last_update=?, meta=?
            WHERE oms_id=?
        """
        params = (
            row.status, row.broker_order_id, row.perm_id, row.filled_qty,
            row.avg_fill_price, row.last_fill_price, datetime.utcnow(), meta_json,
            row.oms_id
        )
        await session.conn.execute(query, params)

    async def load_non_terminal_orders(self) -> List[OrderRow]:
        if not self._conn: return []
        # Define terminal states
        terminals = "('FILLED', 'CANCELED', 'REJECTED', 'EXPIRED')"
        query = f"SELECT * FROM orders WHERE status NOT IN {terminals}"
        
        async with self._conn.execute(query) as cursor:
            rows = await cursor.fetchall()
            return [self._map_row_to_order(r, cursor.description) for r in rows]

    async def load_orders_for_account(self, account_id: AccountId) -> List[OrderRow]:
        if not self._conn: return []
        async with self._conn.execute("SELECT * FROM orders WHERE account_id = ?", (account_id,)) as cursor:
            rows = await cursor.fetchall()
            return [self._map_row_to_order(r, cursor.description) for r in rows]

    # ------------------------------------------------------------------
    # Fills & Positions (Stubs for brevity, but crucial for Phase 1)
    # ------------------------------------------------------------------
    
    async def insert_fill(self, session: DatabaseSession, row: FillRow) -> None:
        assert isinstance(session, SqliteSession)
        query = """
            INSERT INTO fills (oms_id, execution_id, symbol, qty, price, commission, fill_time, meta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        await session.conn.execute(query, (
            row.oms_id, row.execution_id, row.symbol, row.qty, row.price, 
            row.commission, row.fill_time, json.dumps(row.meta)
        ))

    async def has_execution_id(self, execution_id: str) -> bool:
        if not self._conn: return False
        async with self._conn.execute("SELECT 1 FROM fills WHERE execution_id = ?", (execution_id,)) as cursor:
            return await cursor.fetchone() is not None

    async def upsert_position(self, session: DatabaseSession, row: PositionRow) -> None:
        assert isinstance(session, SqliteSession)
        query = """
            INSERT INTO positions (account_id, symbol, qty, avg_price, realized_pnl_today, unrealized_pnl, last_update, meta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(account_id, symbol) DO UPDATE SET
                qty=excluded.qty,
                avg_price=excluded.avg_price,
                last_update=excluded.last_update
        """
        await session.conn.execute(query, (
            row.account_id, row.symbol, row.qty, row.avg_price, 
            row.realized_pnl_today, row.unrealized_pnl, row.last_update, json.dumps(row.meta)
        ))

    # ------------------------------------------------------------------
    # Mappers / Helpers
    # ------------------------------------------------------------------

    def _map_row_to_order(self, row: tuple, description: tuple) -> OrderRow:
        # Helper to map sqlite tuple to OrderRow based on description
        cols = {d[0]: i for i, d in enumerate(description)}
        
        return OrderRow(
            oms_id=OMSId(row[cols['oms_id']]),
            account_id=AccountId(row[cols['account_id']]),
            symbol=Symbol(row[cols['symbol']]),
            side=row[cols['side']],
            qty=row[cols['qty']],
            order_type=row[cols['order_type']],
            time_in_force=row[cols['time_in_force']],
            status=row[cols['status']],
            broker_order_id=row[cols['broker_order_id']],
            perm_id=row[cols['perm_id']],
            limit_price=row[cols['limit_price']],
            stop_price=row[cols['stop_price']],
            filled_qty=row[cols['filled_qty']],
            avg_fill_price=row[cols['avg_fill_price']],
            last_fill_price=row[cols['last_fill_price']],
            # Parse Dates
            created_at=self._parse_date(row[cols['created_at']]),
            last_update=self._parse_date(row[cols['last_update']]),
            meta=json.loads(row[cols['meta']]) if row[cols['meta']] else {}
        )

    def _parse_date(self, val: Any) -> datetime:
        if isinstance(val, datetime): return val
        if isinstance(val, str): 
            try:
                return datetime.fromisoformat(val)
            except:
                pass
        return datetime.utcnow() # Fallback

    # Stubs for interface compliance (You said "Dumb Pipe", so we ignore these for now)
    async def load_fills_for_order(self, oms_id: OMSId) -> List[FillRow]: return []
    async def load_positions_for_account(self, account_id: AccountId) -> List[PositionRow]: return []
    async def get_account_snapshot(self, account_id: AccountId) -> Optional[AccountSnapshotRow]: return None
    async def upsert_account_snapshot(self, session: DatabaseSession, row: AccountSnapshotRow) -> None: pass
    async def append_event_log(self, session: DatabaseSession, row: EventLogRow) -> None: pass
    async def load_event_log(self, limit: Optional[int] = None) -> List[EventLogRow]: return []