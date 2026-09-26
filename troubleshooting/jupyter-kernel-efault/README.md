# VS Code Jupyter Kernel `listen EFAULT` / WinError 10014

Windows 환경에서 VS Code Jupyter Kernel 실행 시 반복적으로 발생한 `listen EFAULT` / `WinError 10014` 문제의 원인 추적 및 해결 기록입니다.

단순 재설치가 아니라 다음 계층을 순서대로 확인하며 문제 범위를 좁혔습니다.

```text
VS Code
→ Jupyter / ipykernel
→ ZeroMQ
→ Python / Node.js Socket
→ Windows Winsock
→ Kernel Driver
```

최종적으로 테스트 환경에서는 **Kings Online Security 커널 드라이버 활성 상태와 Socket `bind/listen` 오류 사이의 강한 인과관계**를 반복 실험으로 확인했습니다.

---

## 1. Error

VS Code Jupyter Kernel 시작 또는 재시작 과정에서 다음 오류가 반복적으로 발생했습니다.

```text
Failed to start the Kernel

listen EFAULT:
bad address in system call argument
127.0.0.1:9005
```

환경에 따라 `0.0.0.0:9000`, `127.0.0.1:9005` 등 주소와 포트는 달라졌습니다.

하위 계층에서는 다음 오류도 확인했습니다.

```text
zmq.error.ZMQError: Bad address

OSError: [WinError 10014]
```

따라서 특정 포트의 단순 충돌 문제는 아니라고 판단했습니다.

---

## 2. Environment

주요 테스트 환경:

- Windows
- VS Code
- Jupyter Extension
- Python 3.12
- ipykernel
- pyzmq / ZeroMQ
- WSL2 / Docker 설치 환경

최초 오류는 **2026-08-18** 관찰되었습니다.

---

## 3. Investigation

문제가 발생하는 계층을 찾기 위해 상위 계층부터 하나씩 제거했습니다.

| 조사 대상 | 테스트 | 결과 |
|---|---|---|
| VS Code / Jupyter | 재설치, Clean Profile, Portable VS Code | 재발 |
| Python 환경 | venv 재생성, ipykernel 재설치 | 재발 |
| Jupyter / ZeroMQ | 최소 ZeroMQ bind 테스트 | `Bad address` 재현 |
| Port | 여러 IP / Port 테스트 | 특정 포트 문제 아님 |
| Python Socket | `bind/listen` 직접 테스트 | `WinError 10014` 재현 |
| Node.js Socket | 별도 런타임 Socket 테스트 | Windows 계층 비교 |
| Winsock | Network Stack 초기화 | 일시 정상화 후 재발 |
| WSL / Docker / Hyper-V | 중지 및 비활성화 | 증상 변화가 있었으나 재발 |
| Kernel Driver | System Driver 조사 | Kings Driver 발견 |

### 핵심 전환점

Jupyter와 ZeroMQ를 제외하고 **Python 기본 Socket만 사용해도 `WinError 10014`가 재현**되었습니다.

```text
Jupyter 문제?
    ↓
ZeroMQ에서도 재현
    ↓
Python Socket에서도 재현
    ↓
Windows Socket / Network 계층으로 조사 범위 축소
```

---

## 4. Test Scripts

조사 및 재현에 사용한 파일입니다.

```text
.
├─ README.md
├─ ajs_test.ipynb
└─ scripts/
   ├─ bind_probe.py
   ├─ bind_probe2.py
   ├─ connectTest.py
   ├─ connectTest.js
   ├─ zmq_test.py
   └─ hook_bind.js
```

- `bind_probe.py` — Socket `bind/listen` 반복 테스트
- `bind_probe2.py` — `bind` / `listen` 실패 단계 구분
- `connectTest.py` — Python Socket 테스트
- `connectTest.js` — Node.js Socket 테스트
- `zmq_test.py` — ZeroMQ 최소 재현 테스트
- `hook_bind.js` — Windows `bind()` 호출 추적
- `ajs_test.ipynb` — Jupyter Kernel 동작 확인

구체적인 테스트 코드는 각 파일을 참고합니다.

---

## 5. Root Cause Investigation

Windows System Driver를 조사하는 과정에서 Kings Online Security 관련 커널 드라이버를 확인했습니다.

```text
KingsNET
State     : Running
StartMode : Auto
Path      : C:\Kings\i-Defense3\KingsNet.sys

KINGS_IDEF
State     : Running
StartMode : Auto
Path      : C:\Kings\i-Defense3\IdefDrv.sys
```

단순 상관관계인지 확인하기 위해 Driver 활성 상태를 변경하며 반복 테스트했습니다.

### A-B-A-B Verification

| Test | Kings Driver | Result |
|---|---|---|
| A1 | ON | `EFAULT / WinError 10014` |
| B1 | OFF | Socket 테스트 + Jupyter 정상 |
| A2 | ON | EFAULT 재현 |
| B2 | OFF | 정상 복구 |

```text
Kings ON  → EFAULT
Kings OFF → 정상
Kings ON  → EFAULT 재현
Kings OFF → 정상 복구
```

동일 환경에서 Driver 활성 상태에 따라 장애 발생과 정상화가 반복되었습니다.

---

## 6. Resolution

테스트 환경에서는 두 Driver의 자동 실행을 비활성화했습니다.

```powershell
sc.exe config KingsNET start= disabled
sc.exe config KINGS_IDEF start= disabled
```

Windows 재부팅 후 다음을 확인했습니다.

- Python Socket 반복 테스트 정상
- VS Code Jupyter Kernel 정상 실행
- Kernel 반복 재시작 정상
- Notebook 전환 후 실행 정상
- Kings Driver 재활성화 시 EFAULT 재현
- 다시 비활성화하면 정상 복구

> **주의**
>
> `KingsNET`, `KINGS_IDEF`는 보안 소프트웨어의 커널 드라이버입니다.
> 비활성화하면 해당 보안 프로그램의 기능에 영향을 줄 수 있습니다.

---

## 7. WSL / Docker와의 관계

확인된 시간 순서는 다음과 같습니다.

```text
2026-07-21
Kings 설치
    ↓
Jupyter 정상

2026-08-18
WSL / Docker 설치
    ↓
EFAULT 최초 관찰
```

WSL/Docker 설치에 따른 Windows 가상화·네트워크 환경 변화가 기존 Kings Driver와의 호환성 문제를 표면화했을 가능성이 있습니다.

다만 이는 **시간적 상관관계를 기반으로 한 가설**이며 WSL/Docker가 직접적인 Trigger였다는 것은 확인하지 못했습니다.

---

## 8. Conclusion

최종 조사 흐름:

```text
Jupyter EFAULT
    ↓
VS Code / Jupyter 문제 배제
    ↓
ZeroMQ에서도 오류 재현
    ↓
Python Socket에서도 WinError 10014 재현
    ↓
Windows Network 계층으로 범위 축소
    ↓
Winsock / WSL / Docker / Hyper-V 조사
    ↓
Kings Kernel Driver 발견
    ↓
A-B-A-B Test
    ↓
Kings ON  → EFAULT
Kings OFF → 정상
```

이번 환경에서는 **Kings Online Security의 `KingsNET` 및/또는 `KINGS_IDEF` 커널 드라이버가 활성화된 상태에서 TCP Socket의 `bind/listen` 처리가 실패하면서 Jupyter Kernel 시작 오류로 이어지는 현상**을 확인했습니다.

다만 아직 확인되지 않은 부분이 있습니다.

- `KingsNET`과 `KINGS_IDEF` 중 어느 Driver가 직접적인 원인인지
- Driver 내부에서 Socket 처리에 영향을 주는 정확한 메커니즘
- WSL/Docker 설치가 최초 장애 발생의 직접적인 Trigger였는지

따라서 이 문제는 단순한 Jupyter 오류가 아니라, **Windows Socket 계층의 문제가 ZeroMQ/ipykernel을 거쳐 VS Code Jupyter Kernel 시작 실패로 나타난 사례**로 정리할 수 있습니다.