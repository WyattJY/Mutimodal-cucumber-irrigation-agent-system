"""Uvicorn loop factory compatible with async psycopg on Windows."""
from __future__ import annotations

import asyncio


def selector_event_loop() -> asyncio.AbstractEventLoop:
    return asyncio.SelectorEventLoop()
