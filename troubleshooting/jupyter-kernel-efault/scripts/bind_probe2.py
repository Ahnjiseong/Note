import socket, sys
host, port, n = sys.argv[1], int(sys.argv[2]), 200
fam = socket.AF_INET6 if ":" in host else socket.AF_INET
res = {}
for _ in range(n):
    s = socket.socket(fam, socket.SOCK_STREAM)
    stage = "bind"
    try:
        s.bind((host, port))
        stage = "listen"
        s.listen()
        k = "OK"
    except OSError as e:
        k = f"{stage}:{e.winerror}"
    finally:
        s.close()
    res[k] = res.get(k, 0) + 1
print(host, port, res)