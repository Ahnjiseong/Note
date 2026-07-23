### 명령어

- 실행: (프로젝트 폴더) conda activate (가상환경 폴더 명)
  실행할 프로젝트의 상위 폴더에서 명령어를 실행

### 가상환경

**<중요>
activate 할 때 실행할 가상환경을 프로젝트 폴더로 할지 conda envs 폴더에 있는 걸로 할지 명시**

1. conda 가상환경 폴더에 만드는 방법(C:\Users\AnJiseong\anaconda3\envs)
- conda activate (가상환경 폴더 명) 으로 바로 실행 가능
- 관리가 편함
- activate가 간단함
2. 프로젝트 폴더에 만드는 방법(진행하는 프로젝트 폴더의 .venv 폴더)
- conda activate (실행할 프로젝트의 위치에서 .venv를 명시)
- 프로젝트 하나만 복사해도 어떤 환경을 사용하는지 명확함
- VS Code가 자동 인식
- GitHub에서 많이 쓰는 구조
