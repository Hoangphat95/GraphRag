import os
import socket
import time

def wait_for(host: str, port: int, timeout: int = 60):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=5):
                return True
        except Exception:
            time.sleep(1)
    return False


if __name__ == '__main__':
    uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    # parse host:port from bolt URI
    try:
        after = uri.split('://', 1)[1]
        host, port = after.split(':')[:2]
        port = int(port)
    except Exception:
        host = 'localhost'
        port = 7687

    ok = wait_for(host, port, timeout=int(os.environ.get('WAIT_TIMEOUT', '60')))
    if not ok:
        raise SystemExit(2)
    print('Neo4j reachable')
