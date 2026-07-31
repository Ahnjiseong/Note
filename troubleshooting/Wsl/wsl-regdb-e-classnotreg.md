## 1. 발생한 문제

Docker Desktop을 실행하기 위해 WSL 상태를 확인하던 중 다음 오류가 발생했다.

```
wsl: WSL 설치가 손상된 것 같습니다.
오류 코드: Wsl/CallMsi/Install/REGDB_E_CLASSNOTREG

아무 키나 눌러 WSL을 복구하거나 CTRL-C 취소하세요.
이 프롬프트는 60초 후 시간이 초과됩니다.
```

다음 명령들도 정상적으로 실행되지 않았다.

```
wsl--versionwsl--status
```

WSL 명령을 실행하면 Windows가 WSL 설치가 손상되었다고 판단해 자동 복구를 시도했지만, 복구 과정에서 `REGDB_E_CLASSNOTREG` 오류가 발생했다.

---



## 2. 오류 코드의 의미

오류 코드:

```
Wsl/CallMsi/Install/REGDB_E_CLASSNOTREG
```

`REGDB_E_CLASSNOTREG`는 일반적으로 다음 의미를 가진다.

```
Class not registered
등록되지 않은 클래스
```

즉, Windows가 WSL 복구나 설치 과정에서 필요한 구성 요소를 호출하려 했지만, 관련 등록 정보나 패키지를 정상적으로 사용하지 못했다는 의미다.

처음에는 다음 가능성을 의심했다.

- Windows 시스템 이미지 손상
- Windows Installer 문제
- WSL 선택적 기능 손상
- WSL 앱 패키지 등록 문제
- 설치된 WSL 버전 문제

---



# 3. 처음 시도한 방법: `wsl_update_x64` 설치

먼저 인터넷에서 WSL 관련 문제 해결 방법을 찾아 `wsl_update_x64.msi`를 설치했다.

하지만 설치 후에도 다음 오류가 그대로 발생했다.

```
Wsl/CallMsi/Install/REGDB_E_CLASSNOTREG
```

## 왜 해결되지 않았는가

`wsl_update_x64.msi`는 주로 예전 방식의 WSL 2 Linux 커널 업데이트 패키지다.

현재 Windows에서는 WSL 자체가 Microsoft Store 앱 패키지로 관리되는 경우가 많다. 따라서 문제가 Store의 WSL 앱이나 패키지 버전에 있다면, 커널 업데이트 MSI만 다시 설치해도 해결되지 않을 수 있다.

즉, 이번 문제는 다음과 같은 상황이었다.

```
WSL 커널 업데이트 패키지 설치
        ↓
Store에 설치된 WSL 앱 문제는 그대로 남음
        ↓
wsl 명령 실행 실패
```

---



# 4. Windows 시스템 이미지 복구 시도

Windows 시스템 파일이나 구성 요소 저장소가 손상되었을 가능성을 확인하기 위해 관리자 PowerShell에서 다음 명령을 실행했다.

```
DISM/Online/Cleanup-Image/RestoreHealth
```

## 명령어의 역할

`DISM`은 Windows 이미지와 구성 요소 저장소를 검사하고 복구하는 도구다.

각 옵션의 의미는 다음과 같다.

```
/Online
현재 실행 중인 Windows를 대상으로 함

/Cleanup-Image
Windows 시스템 이미지 관리 작업을 수행함

/RestoreHealth
손상된 구성 요소를 검사하고 복구함
```

실행 결과 다음 위치에서 진행률이 멈춘 것처럼 보였다.

```
[===========================62.6%====                      ]
```

1시간 이상 진행률이 바뀌지 않아 작업을 중단했다.

## 이 결과에 대한 판단

DISM은 특정 진행률에서 오래 머무는 경우가 있지만, 1시간 이상 아무 변화가 없었기 때문에 별도의 검사 명령을 사용하기로 했다.

다만 이후 검사 결과 Windows 이미지에는 손상이 없었다. 따라서 `RestoreHealth`가 오래 걸린 현상은 이번 WSL 오류의 직접적인 원인이 아니었다.

---



# 5. Windows 구성 요소 저장소 검사

복구 작업 대신 손상 여부만 확인하기 위해 다음 명령을 실행했다.

```
DISM/Online/Cleanup-Image/ScanHealth
```

실행 결과:

```
[==========================100.0%==========================]

손상된 구성 요소 저장소가 검색되지 않았습니다.
작업을 완료했습니다.
```

## 결과 해석

Windows의 구성 요소 저장소에는 손상이 없었다.

따라서 다음 가능성은 낮아졌다.

- Windows 이미지 전체 손상
- DISM 복구가 반드시 필요한 상태
- Windows 재설치가 필요한 심각한 손상

---



# 6. Windows 시스템 파일 무결성 검사

다음으로 Windows 시스템 파일 자체에 문제가 있는지 확인했다.

```
sfc/verifyonly
```

실행 결과:

```
100% 검증 완료

Windows 리소스 보호에서 무결성 위반을 발견하지 못했습니다.
```

## `sfc /verifyonly`의 역할

```
sfc
System File Checker

/verifyonly
시스템 파일을 검사하지만 자동으로 복구하지는 않음
```

## 결과 해석

Windows 핵심 시스템 파일에는 문제가 없었다.

즉, 이번 오류는 Windows 전체가 손상된 문제가 아니라 **WSL 관련 앱이나 패키지에 한정된 문제**일 가능성이 높아졌다.

---



# 7. WSL 선택적 기능 상태 확인

WSL을 사용하려면 Windows의 다음 두 기능이 활성화되어 있어야 한다.

- Linux용 Windows 하위 시스템
- 가상 머신 플랫폼

다음 명령으로 상태를 확인했다.

```
Get-WindowsOptionalFeature `-Online `-FeatureNameMicrosoft-Windows-Subsystem-Linux
```

결과:

```
FeatureName : Microsoft-Windows-Subsystem-Linux
State       : Enabled
```

가상 머신 플랫폼도 확인했다.

```
Get-WindowsOptionalFeature `-Online `-FeatureNameVirtualMachinePlatform
```

결과:

```
FeatureName : VirtualMachinePlatform
State       : Enabled
```

## 결과 해석

두 기능 모두 정상적으로 활성화되어 있었다.

따라서 문제는 다음과 같은 단순 설정 오류가 아니었다.

```
WSL 기능이 꺼져 있음
VirtualMachinePlatform이 꺼져 있음
Windows 기능 활성화 후 재부팅이 필요함
```

---



# 8. Windows 버전 확인

`winver` 명령으로 Windows 버전을 확인했다.

```
winver
```

확인된 환경:

```
Windows 11 Pro
버전 25H2
OS 빌드 26200.8875
```

Windows 버전과 WSL 패키지 사이의 호환성 또는 업데이트 상태도 확인할 필요가 있었다.

---



# 9. WSL 실행 파일 위치 확인

다음 명령으로 실제 실행되는 `wsl.exe`의 위치를 확인했다.

```
where.exewsl
```

결과:

```
C:\Windows\System32\wsl.exe
C:\Users\AnJiseong\AppData\Local\Microsoft\WindowsApps\wsl.exe
```

## 결과 해석

WSL 실행 파일 자체는 존재했다.

첫 번째 경로:

```
C:\Windows\System32\wsl.exe
```

Windows에 포함된 WSL 실행 파일이다.

두 번째 경로:

```
C:\Users\AnJiseong\AppData\Local\Microsoft\WindowsApps\wsl.exe
```

Microsoft Store 앱 실행 별칭과 관련된 경로다.

따라서 문제는 `wsl.exe` 파일이 아예 없어서 발생한 것은 아니었다.

---



# 10. WSL 상태 명령 실행

다음 명령을 실행했다.

```
wsl--status
```

하지만 다시 동일한 오류가 발생했다.

```
wsl: WSL 설치가 손상된 것 같습니다.
오류 코드: Wsl/CallMsi/Install/REGDB_E_CLASSNOTREG
```

## 결과 해석

`wsl.exe`는 정상적으로 발견되지만, WSL 내부 패키지나 설치 정보를 사용하려는 단계에서 실패하고 있었다.

대략적인 흐름은 다음과 같았다.

```
wsl.exe 실행
    ↓
설치된 WSL 패키지 확인
    ↓
손상 또는 업데이트 필요 상태로 판단
    ↓
자동 복구 시도
    ↓
MSI 또는 패키지 호출 과정에서 실패
    ↓
REGDB_E_CLASSNOTREG
```

---



# 11. Windows Installer 로그 확인

Windows Installer와 관련된 오류가 기록되었는지 확인했다.

```
Get-WinEvent-LogNameApplication-MaxEvents30|Where-Object {$_.ProviderName-match"MsiInstaller"
}|Select-ObjectTimeCreated,Id,LevelDisplayName,Message
```

결과는 아무것도 출력되지 않았다.

## 결과 해석

최근 30개의 Application 로그 중 `MsiInstaller` 공급자와 일치하는 이벤트가 없었다.

이는 Windows Installer가 정상이라는 뜻으로 확정할 수는 없지만, 적어도 해당 범위 안에는 관련 오류 로그가 없었다는 의미다.

---



# 12. Windows Installer 서비스 확인

다음 명령으로 Windows Installer 서비스를 확인했다.

```
Get-Servicemsiserver
```

결과:

```
Status   Name       DisplayName
------   ----       -----------
Stopped  msiserver  Windows Installer
```

## `Stopped`여도 괜찮은가

Windows Installer 서비스는 항상 실행되는 서비스가 아니다.

MSI 설치가 필요할 때 자동으로 시작될 수 있으므로, 평상시에 다음처럼 표시되는 것은 반드시 오류가 아니다.

```
Status : Stopped
```

서비스 자체가 존재한다는 점이 중요하다.

또한 다음 명령도 실행했다.

```
msiexec
```

PowerShell에 별도 텍스트 출력은 없었지만, 명령 실행 자체에서 오류가 표시되지는 않았다.

---



# 13. WSL 앱 패키지 설치 상태 확인

처음에는 다음 명령을 실행했다.

```
Get-AppxPackage*WSL*
```

결과가 출력되지 않았다.

하지만 이는 WSL 패키지의 실제 이름에 `WSL`이라는 짧은 문자열이 그대로 포함되지 않아 검색되지 않은 것이었다.

다음 명령을 실행했다.

```
Get-AppxPackage*WindowsSubsystemForLinux*
```

결과:

```
Name              : MicrosoftCorporationII.WindowsSubsystemForLinux
Architecture      : X64
Version           : 2.6.1.0
PackageFullName   : MicrosoftCorporationII.WindowsSubsystemForLinux_2.6.1.0_x64__8wekyb3d8bbwe
Status            : Ok
```

## 결과 해석

WSL Store 앱은 설치되어 있었다.

확인된 정보:

```
패키지 이름:
MicrosoftCorporationII.WindowsSubsystemForLinux

설치 버전:
2.6.1.0

상태:
Ok
```

따라서 WSL 앱이 아예 설치되지 않은 것은 아니었다.

다만 패키지 상태가 `Ok`로 표시되더라도 실제 실행 시 버전이나 등록 정보 문제로 오류가 발생할 수 있다.

---



# 14. WSL 앱 패키지 다시 등록

WSL 앱 패키지의 등록 정보가 꼬였을 가능성을 확인하기 위해 다음 명령을 실행했다.

```
Add-AppxPackage `-Register"C:\Program Files\WindowsApps\MicrosoftCorporationII.WindowsSubsystemForLinux_2.6.1.0_x64__8wekyb3d8bbwe\AppxManifest.xml" `-DisableDevelopmentMode
```

PowerShell에서 별도의 오류는 출력되지 않았다.

## 명령어의 역할

```
Add-AppxPackage
Windows 앱 패키지를 설치하거나 등록함

-Register
이미 존재하는 AppxManifest.xml을 이용해 앱을 다시 등록함

-DisableDevelopmentMode
개발 모드 앱이 아닌 일반 앱 패키지로 등록함
```

하지만 이 작업만으로는 WSL 오류가 해결되지 않았다.

즉, 단순 재등록보다 **WSL 앱을 최신 버전으로 업데이트하는 작업**이 필요했다.

---



# 15. 최종 해결 방법

Microsoft Store를 실행한 뒤 WSL 앱을 업데이트했다.

대략적인 경로:

```
Microsoft Store 실행
    ↓
라이브러리
    ↓
업데이트 확인
    ↓
Windows Subsystem for Linux 업데이트
```

또는 Store에서 다음 앱을 직접 검색해 업데이트할 수 있다.

```
Windows Subsystem for Linux
```

업데이트 후 다음 명령을 다시 실행했다.

```
wsl--version
```

이번에는 정상적으로 WSL 버전 정보가 출력되었다.

Docker Desktop도 다시 실행했으며, 정상적으로 Running 상태가 되었다.



# 16. 최종 원인 정리

이번 문제의 직접적인 원인은 Windows 시스템 이미지 손상이 아니었다.

검사 결과:

```
DISM /ScanHealth
→ 구성 요소 저장소 손상 없음

sfc /verifyonly
→ 시스템 파일 무결성 위반 없음

WSL 선택적 기능
→ Enabled

VirtualMachinePlatform
→ Enabled

WSL 앱 패키지
→ 설치되어 있음
```

최종적으로 Microsoft Store에서 WSL 앱을 업데이트하자 문제가 해결되었다.

따라서 가장 가능성 높은 원인은 다음과 같다.

> **설치되어 있던 Store 버전 WSL 패키지가 현재 Windows 환경과 정상적으로 동작하지 않거나, 업데이트가 필요한 상태였음**
> 

오류 발생 구조를 정리하면 다음과 같다.

```
Windows의 WSL 기능은 활성화됨
        ↓
Store WSL 앱도 설치되어 있음
        ↓
하지만 기존 WSL 앱의 버전 또는 설치 상태에 문제 발생
        ↓
wsl.exe가 자동 복구를 시도
        ↓
복구 과정에서 REGDB_E_CLASSNOTREG 발생
        ↓
Microsoft Store에서 WSL 업데이트
        ↓
WSL 정상 실행
        ↓
Docker Desktop 정상 실행
```

---



# 17. 해결 과정 요약

```
1. wsl --version 실행
   → WSL 설치 손상 및 REGDB_E_CLASSNOTREG 오류 발생

2. wsl_update_x64.msi 설치
   → 해결되지 않음

3. DISM /RestoreHealth 실행
   → 62.6%에서 1시간 이상 정체

4. DISM /ScanHealth 실행
   → Windows 구성 요소 저장소 손상 없음

5. sfc /verifyonly 실행
   → 시스템 파일 무결성 위반 없음

6. WSL 선택적 기능 확인
   → Enabled

7. VirtualMachinePlatform 확인
   → Enabled

8. where.exe wsl 실행
   → wsl.exe 파일 정상 존재

9. wsl --status 실행
   → 동일 오류 재현

10. WSL Appx 패키지 확인
    → MicrosoftCorporationII.WindowsSubsystemForLinux 설치 확인
    → 버전 2.6.1.0

11. WSL 패키지 재등록
    → 명령은 성공했지만 문제 지속

12. Microsoft Store에서 WSL 업데이트
    → 문제 해결

13. wsl --version 확인
    → 정상 출력

14. Docker Desktop 실행
    → 정상 Running
```

---



# 18. 동일 오류 발생 시 권장 해결 순서

다음과 같은 오류가 다시 발생할 경우:

```
Wsl/CallMsi/Install/REGDB_E_CLASSNOTREG
```

먼저 복잡한 Windows 복구 작업보다 Microsoft Store 업데이트부터 확인하는 것이 효율적이다.

## 1단계: Microsoft Store에서 WSL 업데이트

```
Microsoft Store
→ 라이브러리
→ 업데이트 확인
→ Windows Subsystem for Linux 업데이트
```

## 2단계: WSL 상태 확인

```
wsl--versionwsl--status
```

## 3단계: Windows 기능 확인

```
Get-WindowsOptionalFeature `-Online `-FeatureNameMicrosoft-Windows-Subsystem-Linux
```

```
Get-WindowsOptionalFeature `-Online `-FeatureNameVirtualMachinePlatform
```

두 기능 모두 다음 상태여야 한다.

```
State : Enabled
```

## 4단계: WSL 앱 패키지 확인

```
Get-AppxPackage*WindowsSubsystemForLinux*
```

## 5단계: Windows 손상 여부 확인

```
DISM/Online/Cleanup-Image/ScanHealth
```

```
sfc/verifyonly
```

Windows 손상이 확인된 경우에만 다음 복구 명령을 고려한다.

```
DISM/Online/Cleanup-Image/RestoreHealth
```

```
sfc/scannow
```

---



# 19. 이번 해결 과정에서 알게 된 점

## `Get-AppxPackage *WSL*` 결과가 없다고 WSL이 미설치된 것은 아니다

실제 패키지 이름은 다음과 같았다.

```
MicrosoftCorporationII.WindowsSubsystemForLinux
```

따라서 다음 검색어를 사용하는 것이 더 정확하다.

```
Get-AppxPackage*WindowsSubsystemForLinux*
```

---

## `msiserver`가 Stopped여도 반드시 문제가 있는 것은 아니다

Windows Installer는 필요할 때 자동으로 실행되는 서비스다.

따라서 다음 상태만으로는 오류라고 판단할 수 없다.

```
Status : Stopped
```

---

## `wsl_update_x64`는 최신 Store WSL 앱 업데이트와 다르다

```
wsl_update_x64
→ 주로 WSL 2 Linux 커널 업데이트

Microsoft Store의 WSL 업데이트
→ WSL 앱 전체 업데이트
```

이번 문제는 Store 앱 업데이트로 해결되었기 때문에, 커널 MSI만 설치해서는 해결되지 않았다.

---

## DISM 정체가 곧 Windows 손상을 의미하는 것은 아니다

`RestoreHealth`가 오래 정체되었지만 다음 검사에서는 손상이 발견되지 않았다.

```
DISM /ScanHealth
→ 손상 없음

sfc /verifyonly
→ 무결성 위반 없음
```

따라서 이번 경우에는 Windows 재설치나 인플레이스 복구까지 진행할 필요가 없었다.

---

# 결론

이번 오류는 Windows 시스템 자체의 손상보다는 **Microsoft Store에 설치된 WSL 앱의 업데이트 상태 문제**였다.

최종 해결 방법은 다음 한 줄로 정리할 수 있다.

> **Microsoft Store에서 Windows Subsystem for Linux 앱을 업데이트한 뒤 WSL과 Docker Desktop이 정상적으로 실행되었다.**
>
