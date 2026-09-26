import zmq

ok = 0
fail = 0
errors = []

for i in range(100):
    s = None
    try:
        s = zmq.Context.instance().socket(zmq.ROUTER)
        s.bind("tcp://127.0.0.1:*")
        ok += 1
    except Exception as e:
        fail += 1
        errors.append((i, repr(e)))
    finally:
        if s is not None:
            s.close()

print(f"ZMQ OK = {ok}")
print(f"ZMQ FAIL = {fail}")
if errors:
    print("첫 번째 실패 예시:", errors[0])