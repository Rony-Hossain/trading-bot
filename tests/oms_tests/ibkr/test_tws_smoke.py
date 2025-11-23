import os
import asyncio
import pytest

try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv()
except ImportError:
    pass

from src.order_management_system.brokers.ibkr.async_adapter import IbkrAsyncAdapter
from src.order_management_system.brokers.ibkr.ibkr_config import IbkrConfig

pytestmark = pytest.mark.skipif(
    os.getenv("IBKR_LIVE_TEST") != "1",
    reason="Set IBKR_LIVE_TEST=1 to run live IBKR tests",
)

@pytest.mark.asyncio
async def test_async_adapter_connect_and_time():
    """
    Live smoke test for IbkrAsyncAdapter:

    - start() should connect
    - get_broker_time() should return a datetime
    - stop() should cleanly disconnect
    """
    config = IbkrConfig(
        host=os.getenv("IBKR_HOST", "127.0.0.1"),
        port=int(os.getenv("IBKR_PORT", "7497")),
        client_id=int(os.getenv("IBKR_CLIENT_ID", "17")),
        account_id=os.getenv("IBKR_ACCOUNT_ID", "DU0000000"),
    )

    adapter = IbkrAsyncAdapter(config=config)

    await adapter.start()
    assert adapter.is_connected(), "Adapter thinks it is not connected after start()"

    broker_time = await adapter.get_broker_time()
    print(f"Adapter broker time: {broker_time!r}")
    assert broker_time is not None

    await adapter.stop()
