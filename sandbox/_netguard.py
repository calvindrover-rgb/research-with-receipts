"""Local-mode egress guard: refuse DNS for any host not on pubdata's allowlist."""
import socket, pubdata
_orig = socket.getaddrinfo
def _guard(host, *a, **k):
    if host not in pubdata.ALLOW:
        raise PermissionError(f"BLOCKED by sandbox policy: {host} is not an allowlisted public-data host")
    return _orig(host, *a, **k)
socket.getaddrinfo = _guard
