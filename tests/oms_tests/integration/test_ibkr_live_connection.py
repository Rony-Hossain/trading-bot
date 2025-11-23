# tests/oms_tests/integration/test_ibkr_live_connection.py
import asyncio
import os
import pytest

from src.order_management_system.brokers.ibkr.async_adapter import IbkrAsyncAdapter
from src.order_management_system.brokers.ibkr.ibkr_config import IbkrConfig

# Optional: load from .env if you want (only if you're using python-dotenv)
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv()
except ImportError:
    pass

pytestmark = pytest.mark.skipif(
    os.getenv("IBKR_LIVE_TEST") != "1",
    reason="Set IBKR_LIVE_TEST=1 (or in .env) to run live IBKR tests",
)

@pytest.mark.asyncio
async def test_ibkr_live_connect_and_time():
    config = IbkrConfig(
        host=os.getenv("IBKR_HOST", "127.0.0.1"),
        port=int(os.getenv("IBKR_PORT", "7497")),
        client_id=int(os.getenv("IBKR_CLIENT_ID", "1")),
        account_id=os.getenv("IBKR_ACCOUNT_ID", ""),
    )

    adapter = IbkrAsyncAdapter(config=config)

    await adapter.start()
    broker_time = await adapter.get_broker_time()
    await adapter.stop()

    assert broker_time is not None

def test_ibkr_live_connect_and_time():
    """
    Simple smoke test:

    - Connect to TWS/Gateway
    - Call reqCurrentTime()
    - Assert we got a valid response
    """
    host = os.getenv("IBKR_HOST", "127.0.0.1")
    port = int(os.getenv("IBKR_PORT", "7497"))
    client_id = int(os.getenv("IBKR_CLIENT_ID", "17"))  # pick any free clientId

    ib = IB()
    ib.connect(host, port, clientId=client_id)

    # If connection fails, ib.isConnected() will be False or raise
    assert ib.isConnected(), "Failed to connect to IBKR TWS/Gateway"

    current_time = ib.reqCurrentTime()
    print(f"IBKR server time: {current_time!r}")

    assert current_time is not None

    ib.disconnect()