"""
Nymo Relay Server — WebSocket версия для Railway
"""
import asyncio
import websockets
import os

PORT  = int(os.environ.get("PORT", 8080))
rooms = {}

async def handler(ws):
    room_id = None
    try:
        room_id = await ws.recv()
        print(f"[+] комната: {room_id}")

        if room_id not in rooms:
            rooms[room_id] = ws
            await ws.send("WAIT")
            print(f"    {room_id}: ждём второго...")
            deadline = asyncio.get_event_loop().time() + 180
            while room_id in rooms:
                if asyncio.get_event_loop().time() > deadline:
                    await ws.send("TIMEOUT")
                    return
                await asyncio.sleep(0.3)
            await asyncio.sleep(3600)
        else:
            partner = rooms.pop(room_id)
            await partner.send("CONNECT")
            await ws.send("CONNECT")
            print(f"    {room_id}: пайп запущен")
            async def fwd(src, dst):
                try:
                    async for msg in src:
                        await dst.send(msg)
                except: pass
                finally:
                    try: await dst.close()
                    except: pass
            await asyncio.gather(fwd(ws, partner), fwd(partner, ws))

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"[-] {e}")
    finally:
        if room_id and rooms.get(room_id) == ws:
            del rooms[room_id]

async def main():
    print(f"Nymo Relay запущен на порту {PORT}")
    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()

asyncio.run(main())
