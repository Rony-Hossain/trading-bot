Execution Layer Architecture
Unified, Safe, Broker-Agnostic Trade Execution for the Trading Bot
🚀 Purpose

The goal of the new execution layer is simple:

Provide a single, safe, reliable system that executes trades against IBKR (and future brokers) without exposing broker complexity to the strategy layer.

Your trading bot does NOT talk to TWS, contracts, ib_insync quirks, orderIds, fill events, reconciling, etc.

It talks to:

broker.submit_order(Order(...))
broker.cancel(order_id)
broker.get_position("SPY")


And the Execution Engine does everything else.

🧱 High-Level Architecture
trading-bot/
├── src/
│   ├── execution/            ← Core execution stack (broker-agnostic)
│   │   ├── engine.py
│   │   ├── types.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── ib/
│   │       ├── connector.py
│   │       └── utils.py
│   │
│   ├── broker_api.py         ← Generic API used by core strategy
│   ├── core_strategy.py
│   └── …
│
├── engines/
│   └── ibkr/
│       ├── adapter.py        ← Implementation of BrokerAPI using ExecutionEngine
│       └── old_adapter.py
│
├── config/
│   └── execution.py
│
├── run_live.py
├── run_paper.py
└── requirements.txt

🎯 Design Goals
✔ Broker-agnostic interface

Strategy code speaks to BrokerAPI.
The adapter routes that to the ExecutionEngine → IBKR.

✔ One canonical Order model

Only one Order dataclass exists in the project (src/execution/types.py).
Used by strategies, backtests, broker adapters, and the execution engine.

✔ Full order lifecycle tracking

Every order goes through:

NEW → WORKING → PARTIALLY_FILLED → FILLED | CANCELED | REJECTED

✔ Partial fill handling

The engine tracks incremental fills and aggregate fill stats:

filled quantity

average fill price

timestamps

✔ Reconciliation after restart

If TWS or your process restarts, the engine scans open orders and re-attaches them.

✔ End-of-day flattening

One call:

engine.flatten_all()

✔ Structured logging

Console + file logging for:

order submissions

cancellations

status changes

fills

reconciling

connection issues

✔ Future-proof

ExecutionEngine is broker-agnostic.
IBKR-specific logic sits in src/execution/ib/.

Later, adding Webull/Moomoo is trivial: create a new adapter + a new connector.

🧩 Responsibilities Breakdown
1. src/execution/types.py
Defines all execution-related domain objects

Order

OrderState

ExecStatus

This file defines the canonical order schema.
Every part of the system uses this exact Order.

No more duplicate Order types.

2. src/execution/config.py
Configuration only

Example fields:

host

port

client_id

account

reconnect attempts

reconnect delay

No logic here — just configuration.

3. src/execution/logging.py
Central logger for the entire execution layer

Outputs to:

STDOUT

logs/execution.log

Format:

2025-01-11 09:10:54 | INFO     | execution.engine | SUBMIT | BUY 1 SPY LIMIT @ 495.00


Provides:

Post-mortem debugging

Replayable logs

Live monitoring visibility

4. src/execution/engine.py
The heart of the execution system

This is the core engine that all brokers will use.

Responsibilities:
✔ Connecting to the broker

Handles reconnects

Handles disconnect events

Tracks connection health

✔ Submitting orders

Build contracts

Build market/limit orders

Place order

Generate oms_id

Track OrderState

✔ Receiving events

From broker → via connector:

Order status updates → update state

Fills → compute delta, update state

✔ Reconciliation on startup

Query open broker orders

Rebuild OrderState

Reattach event handlers

Avoid orphan orders

✔ Position management

positions()

flatten_all()

✔ Logging

Every event gets logged.

5. src/execution/ib/connector.py
IBKR-specific code isolated here

Contract qualification

Symbol mapping

ib_insync quirks and helpers

This avoids polluting your clean engine with broker-specific weirdness.

6. engines/ibkr/adapter.py
Implements BrokerAPI using ExecutionEngine

This is what CoreStrategy interacts with.

Responsibilities:

Convert API calls → ExecutionEngine calls

Never expose IBKR internals

Provide broker metrics:

cash()

equity()

position(symbol)

now()

This file is tiny and stable.

7. run_paper.py & run_live.py
Entry points for actual trading

Both scripts:

Load execution config

Initialize IB instance

Build IBKRExecutionBroker

Attach fill/status callbacks (optional)

Launch strategy

The only difference between live & paper is config.

📈 Lifecycle & Control Flow
Strategy says:
oms_id = broker.submit_order(Order(...))

Broker adapter:
→ engine.submit(order)

ExecutionEngine:
1. Connect to IBKR
2. Build contract
3. Submit order
4. Store OrderState(oms_id ↔ ib_order_id)
5. Attach event listeners
6. Emit SUBMIT log

IBKR sends events:

orderStatusEvent → _on_status

fillEvent → _on_fill

Engine updates state, logs, triggers callbacks.

🛡 Safety Layers
1. Logging

Everything is logged:
SUBMIT / STATUS / FILL / CANCEL / RECONCILE

2. Reconnection

Engine auto-reconnects on next call after disconnect.

3. Reconciliation

On startup:

find open orders

rebuild OrderState

attach listeners

update strategy about recovered orders

4. End-of-day flatten rule

Run once daily (15:50):

engine.flatten_all()


Keeps you out of PDT/regulatory trouble.

5. Trading enabled flag

Your strategy’s config still controls:

Config(trading_enabled=True)


Disables submissions but logs signals.

🔧 Development Phases (Recommended)

This is how you safely build and ship the engine:

Phase 0: Wire the structure — no trading

Add folders

Add types

Add config

Add logging

Import everything successfully

Phase 1: Minimal market-only submit

Submit market orders in paper

Ensure SUBMIT / FILLED events log correctly

Test cancellation

Phase 2: Limit orders + partial fill logic

Add limit support

Partial fill status transitions

Better avg price logic

Phase 3: Reconciliation

Submit a GTC

Kill process

Restart

Verify order still tracked

Phase 4: Flatten rule

Test flatten_all

Add 3:50 PM scheduler

Phase 5: Options

Add fields

Add option contract building

Test paper fills

🧠 Why This Architecture Works Long-Term
✦ Single source of truth for orders

OrderState in ExecutionEngine is the authoritative state, not IB.

✦ One execution engine for all brokers

Later, you can add:

WebullExecutionEngine

AlpacaExecutionEngine

MoomooExecutionEngine

Then create a RoutingEngine that picks which engine to use — same API.

✦ Strategies remain broker-agnostic

All your alpha/risk logic stays untouched.

✦ Easier debugging

Structured logs → reproducible trade history even after crashes.

✦ Safe upgrades

You can:

add persistence

add multi-leg options

add CVaR sizing

add VWAP execution
without breaking strategy logic.

📜 Final Summary

This documentation describes a clean, scalable, and safe execution architecture that:

Centralizes execution logic

Standardizes order lifecycle

Supports restarts and reconciling

Protects against catastrophic live failures

Enables future multi-broker expansion

Keeps your strategy layer clean

It’s the right plan, and now you have a professional-level spec.