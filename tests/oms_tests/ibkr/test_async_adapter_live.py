import os
import pytest
# NOTE: Using the standard import for clarity
from ib_insync import IB, util
from datetime import datetime
import asyncio  # Explicitly import asyncio

# ----------------------------------------------------------------------------
# CRITICAL NOTE:
# 1. REMOVE util.startLoop() when using pytest-asyncio. It causes conflicts.
# 2. Use the 'async' fixture mode, which automatically handles the event loop.
# ----------------------------------------------------------------------------
# util.startLoop() # <-- REMOVED!

# ------------------------------------------------------------
# LIVE TEST SAFETY SWITCH
# ------------------------------------------------------------
pytestmark = pytest.mark.skipif(
    os.getenv("IBKR_LIVE_TEST") != "1",
    reason="Set IBKR_LIVE_TEST=1 to run live IBKR tests",
)


# CRITICAL FIX: Make the test function an async coroutine
@pytest.mark.asyncio
async def test_ibkr_live_connect_and_time():
    """
    Simple smoke test using explicit async calls for robust integration
    with ib_insync and pytest-asyncio.
    """

    # Fix the tuple assignment bug (removed trailing comma)
    host = os.getenv("IBKR_HOST", "127.0.0.1")
    port = int(os.getenv("IBKR_PORT", "7497"))
    client_id = int(os.getenv("IBKR_CLIENT_ID", "17"))
    # FIX: Account ID assignment was creating a tuple, which ib_insync doesn't like.
    account_id = os.getenv("IBKR_ACCOUNT_ID", "DU0000000")

    ib = IB()

    try:
        # 1. Connect to TWS/Gateway.
        # CRITICAL FIX: Use the explicit async connect method and await it
        await ib.connectAsync(
            host,
            port,
            clientId=client_id,
            timeout=5,
            # account_id is not a parameter for connect, only for reqAccountSummary
            # account_id=account_id
        )

        # Sanity check
        assert ib.isConnected(), "❌ Failed to connect to IBKR TWS/Gateway"

        # 2. Call reqCurrentTime() - CRITICAL FIX: Use the async version and await it
        current_time: datetime = await ib.reqCurrentTimeAsync()
        print(f"IBKR server time: {current_time!r}")

        # 3. Ensure a valid response is received.
        assert current_time is not None, "❌ reqCurrentTime() returned None"
        assert isinstance(current_time, datetime), "❌ reqCurrentTime() did not return a datetime object"

    except asyncio.CancelledError:
        pytest.fail("Test was cancelled, possibly due to disconnection.")
    except Exception as e:
        # Catch connection or runtime errors from the awaited calls
        pytest.fail(f"Test failed during IBKR execution: {e}", pytrace=False)

    finally:
        # Cleanly disconnect
        if ib.isConnected():
            ib.disconnect()
