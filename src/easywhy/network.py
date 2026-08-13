from dataclasses import dataclass

import psutil

# Loopback and unspecified addresses aren't "using your internet".
_LOCAL_PREFIXES = ("127.", "::1", "0.0.0.0", "::", "169.254.", "fe80:")


@dataclass(slots=True)
class NetProc:
    pid: int
    name: str
    connections: int
    remotes: list[str]


def _is_external(raddr) -> bool:
    if not raddr or not raddr.ip:
        return False
    return not raddr.ip.startswith(_LOCAL_PREFIXES)


def per_process() -> list[NetProc]:
    """Ranks processes by how many active external connections they hold.

    psutil doesn't expose per-process byte counts in a way that works the same
    on all three platforms, so this attributes network activity by connection
    count — the app holding the most live remote sockets is the most likely
    source of unexpected traffic. Best-effort, and clearly presented as such."""
    counts: dict[int, dict] = {}
    try:
        conns = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, OSError):
        return []

    for conn in conns:
        if conn.pid is None or conn.status == psutil.CONN_LISTEN:
            continue
        if not _is_external(conn.raddr):
            continue
        entry = counts.setdefault(conn.pid, {"count": 0, "remotes": set()})
        entry["count"] += 1
        entry["remotes"].add(conn.raddr.ip)

    out = []
    for pid, data in counts.items():
        try:
            name = psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            name = f"pid {pid}"
        out.append(NetProc(pid, name, data["count"], sorted(data["remotes"])[:6]))

    out.sort(key=lambda p: p.connections, reverse=True)
    return out


def top_connection_holder() -> str | None:
    procs = per_process()
    if procs and procs[0].connections >= 3:
        return procs[0].name
    return None
