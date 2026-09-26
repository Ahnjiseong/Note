import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("192.168.219.195", 9005))
s.listen(1)

print("SUCCESS")


s.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("127.0.0.1", 9005))
s.listen(1)

print("LOCALHOST SUCCESS")