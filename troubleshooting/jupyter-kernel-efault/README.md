# VS Code Jupyter Kernel `listen EFAULT` / WinError 10014

Windows 환경에서 VS Code Jupyter Kernel 실행 시 반복적으로 발생한 `listen EFAULT` / `WinError 10014` 문제의 원인 추적 및 해결 기록입니다.

단순 재설치가 아닌 **VS Code → Jupyter → ZeroMQ → Python Socket → Windows Network → Kernel Driver** 순서로 문제 범위를 좁혔으며, 최종적으로 Kings Online Security 커널 드라이버 활성 상태와 오류 사이의 인과관계를 반복 실험으로 확인했습니다.

---

## 1. Error

대표적으로 다음과 같은 오류가 발생했습니다.

```text
Failed to start the Kernel

listen EFAULT:
bad address in system call argument
127.0.0.1:9005
```

Python / ZeroMQ 계층에서는 다음 오류도 확인했습니다.

```text
zmq.error.ZMQError: Bad address
```

```text
OSError: [WinError 10014]
```

오류에 표시되는 포트는 `9000`, `9001`, `9005` 등으로 달라졌으며 특정 포트에 고정된 문제는 아니었습니다.

---

## 2. Environment

문제가 발생한 주요 환경:

* Windows
* VS Code
* Jupyter Extension
* Python 3.12
* ipykernel
* pyzmq / ZeroMQ
* WSL2 / Docker 설치 환경

최초 오류는 **2026-08-18** 관찰되었습니다.

---

## 3. Investigation

문제 발생 계층을 찾기 위해 다음 순서로 범위를 좁혔습니다.

| 조사 대상                  | 테스트                                                   | 결과                  |
| ---------------------- | ----------------------------------------------------- | ------------------- |
| VS Code / Jupyter      | Extension 재설치, 버전 변경, Clean Profile, Portable VS Code | 재발                  |
| Python 환경              | venv 재생성, ipykernel 재설치                               | 재발                  |
| Jupyter Server         | 직접 Server / ipykernel 실행                              | VS Code 밖에서도 재현     |
| ZeroMQ                 | 최소 `zmq.bind()` 테스트                                   | `Bad address` 재현    |
| Port                   | `netstat`, 고정 포트 테스트                                  | 단순 포트 충돌 아님         |
| Python Socket          | `socket.bind/listen()` 직접 테스트                         | `WinError 10014` 재현 |
| Winsock / TCP-IP       | Network Stack 초기화                                     | 일시 정상화 후 재발         |
| WSL / Docker / Hyper-V | 관련 기능 중지 및 비활성화                                       | 증상 변화 있으나 재발        |
| Kernel Driver          | System Driver 조사                                      | Kings Driver 발견     |

### 핵심 전환점

Jupyter와 ZeroMQ를 제외하고 Python 표준 Socket만 사용해도 동일한 계열의 오류가 발생했습니다.

```python
import socket

s = socket.socket()
s.bind(("127.0.0.1", 9555))
s.listen()
```

결과:

```text
OSError: [WinError 10014]
```

따라서 문제는 VS Code나 Jupyter 자체보다 낮은 **Windows Socket / Network 계층**에서 발생하고 있다고 판단했습니다.

관련 재현 코드는 [`scripts/`](./scripts/)에 정리했습니다.

---

## 4. Root Cause Investigation

Windows에 등록되어 실제 실행 중인 System Driver를 조사하는 과정에서 다음 두 Kings Online Security 커널 드라이버를 발견했습니다.

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

Kings 관련 파일은 2026-07-21 설치되어 있었으며, Jupyter EFAULT는 2026-08-18부터 관찰되었습니다.

---

## 5. A-B-A-B Verification

단순 상관관계인지 확인하기 위해 다른 환경은 유지하고 Kings Driver의 활성 상태를 변경하며 반복 테스트했습니다.

| Test | Kings Driver | Result                           |
| ---- | ------------ | -------------------------------- |
| A1   | ON           | `EFAULT / WinError 10014`        |
| B1   | OFF          | Socket 1000/1000 성공 + Jupyter 정상 |
| A2   | ON           | `127.0.0.1:9005 EFAULT` 재현       |
| B2   | OFF          | Jupyter 정상 복구                    |

결과:

```text
Kings ON
    ↓
EFAULT

Kings OFF
    ↓
정상

Kings ON
    ↓
EFAULT 재현

Kings OFF
    ↓
정상 복구
```

동일 환경에서 활성 상태에 따라 장애 발생과 정상화가 반복되어 **Kings 커널 드라이버 활성 상태와 EFAULT 발생 사이의 강한 인과관계**를 확인했습니다.

---

## 6. Resolution

테스트 환경에서는 다음과 같이 두 드라이버의 자동 실행을 비활성화했습니다.

```powershell
sc.exe config KingsNET start= disabled
sc.exe config KINGS_IDEF start= disabled
```

이후 Windows를 재부팅했습니다.

결과:

* Python Socket 반복 테스트 `1000/1000` 성공
* VS Code Jupyter Kernel 정상 실행
* Kernel 반복 재시작 정상
* Notebook 전환 후 실행 정상
* Kings Driver 재활성화 시 EFAULT 재현
* 다시 비활성화하면 정상 복구

> [!WARNING]
> `KingsNET` 및 `KINGS_IDEF`는 보안 소프트웨어의 커널 드라이버입니다.
> 드라이버 비활성화는 해당 보안 프로그램의 기능에 영향을 줄 수 있습니다.
> 관리되는 PC에서는 임의로 비활성화하지 말고 시스템 관리자 또는 소프트웨어 공급업체의 안내를 확인해야 합니다.

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
같은 날 EFAULT 최초 관찰
```

따라서 WSL/Docker 설치에 따른 Windows 가상화·네트워크 환경 변화가 기존 Kings Driver와의 호환성 문제를 표면화했을 가능성이 있습니다.

하지만 이 부분은 **시간적 상관관계를 기반으로 한 가설**이며, WSL/Docker가 직접적인 Trigger였다는 것은 확인하지 못했습니다.

---

## 8. Conclusion

최종적으로 확인한 문제 흐름은 다음과 같습니다.

```text
Jupyter EFAULT
    ↓
VS Code / Jupyter 배제
    ↓
Python / pyzmq 배제
    ↓
Python Socket에서도 WinError 10014
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

이번 환경에서는 **Kings Online Security의 `KingsNET` 및/또는 `KINGS_IDEF` 커널 드라이버가 활성화된 상태에서 localhost TCP Socket의 `bind/listen` 처리가 실패하면서 Jupyter Kernel 시작 오류로 이어지는 현상**을 확인했습니다.

다만 다음 사항은 아직 확인되지 않았습니다.

* `KingsNET`과 `KINGS_IDEF` 중 어느 드라이버가 직접적인 원인인지
* Driver 내부에서 Socket 처리에 영향을 주는 정확한 메커니즘
* WSL/Docker 설치가 최초 장애 발생의 직접적인 Trigger였는지
