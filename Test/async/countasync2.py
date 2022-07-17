#!/usr/bin/env python3
# countasync.py

import asyncio
import time

async def count():
    print("One")
    await f()
    print("Two")

async def f():
    await asyncio.sleep(3)

async def main():
    await asyncio.gather(count(), count(), count())

if __name__ == "__main__":
    import time
    s = time.perf_counter()
    asyncio.run(main())
    elapsed = time.perf_counter() - s
    print(f"{__file__} executed in {elapsed:0.2f} seconds.")
