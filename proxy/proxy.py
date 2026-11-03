"""Egress allowlist proxy: the sandbox network has no route to the internet except through here."""
import asyncio, os
ALLOW = set(os.environ.get("ALLOW_HOSTS", "").split(","))
async def pipe(r, w):
    try:
        while (d := await r.read(65536)): w.write(d); await w.drain()
    except Exception: pass
    finally: w.close()
async def handle(r, w):
    line = (await r.readline()).decode()
    while (await r.readline()) not in (b"\r\n", b""): pass
    parts = line.split()
    if len(parts) < 2 or parts[0] != "CONNECT":
        w.write(b"HTTP/1.1 405 CONNECT only\r\n\r\n"); w.close(); return
    host, port = parts[1].rsplit(":", 1)
    if host not in ALLOW:
        print(f"DENY {host}", flush=True); w.write(b"HTTP/1.1 403 Blocked by sandbox egress policy\r\n\r\n"); w.close(); return
    ur, uw = await asyncio.open_connection(host, int(port))
    w.write(b"HTTP/1.1 200 OK\r\n\r\n"); await w.drain(); print(f"ALLOW {host}", flush=True)
    await asyncio.gather(pipe(r, uw), pipe(ur, w))
async def main():
    s = await asyncio.start_server(handle, "0.0.0.0", 3128); await s.serve_forever()
if __name__ == "__main__": asyncio.run(main())
