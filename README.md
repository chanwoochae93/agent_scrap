# 🚀 WebDev & AI Trends Multi-Agent System (v4.0)

**4개의 전문 AI 에이전트가 협력하여 매주 최신 FE 트렌드를 수집, 분석, 리포팅하고 스스로 학습/개선하는 완전 자동화 시스템**

---

## 🤖 핵심 아키텍처 (v4.0)

이 시스템은 4개의 독립적인 AI 에이전트가 체계적으로 협력합니다.

1.  **🤖 Agent 1: 정보 수집가 (Collector)**
    -   웹에서 최신 기술 정보를 수집하고, **Gemini AI를 이용해 1차적으로 유의미한 정보를 필터링**합니다.

2.  **🧠 Agent 2: AI 분석가 (Analyzer)**
    -   정제된 정보를 심층 분석하여 **새로운 HTML/CSS 기술 리포트**를 생성합니다.
    -   **새로운 트렌드 키워드를 제안**하고, **오래된 키워드를 식별**하여 시스템이 스스로 진화하도록 돕습니다.

3.  **✉️ Agent 3: 이메일 디자이너 (Emailer)**
    -   분석 리포트를 바탕으로 **Gemini AI가 직접 시각적으로 매력적인 HTML 이메일**을 디자인하고 발송합니다.

4.  **🛠️ Agent 4: 코드 리뷰어 (Code Reviewer)**
    -   매주 우리 **프로젝트의 전체 코드를 스스로 분석**하고 개선점을 찾아 리포트로 작성합니다.

## 🎨 작동 방식 (Workflow)

```mermaid
graph TD
    A[매주 월요일 10시] --> B(Orchestrator 시작)
    B --> C{1. Collector Agent 실행}
    C --> D[웹 데이터 수집]
    D --> E[AI로 1차 필터링]
    E --> F{2. Analyzer Agent 실행}
    F --> G[AI 심층 분석 및 리포트 생성]
    G --> H[키워드 제안/정리]
    H --> I{3. Emailer Agent 실행}
    I --> J[AI가 HTML 이메일 생성]
    J --> K[이메일 발송]
    H --> L{4. 설정 자동 업데이트}
    L --> M[config.py에 키워드 추가/제거]
    B --> N{5. Code Reviewer 실행}
    N --> O[프로젝트 코드 분석]
    O --> P[개선점 리포트 저장]