# University Ranking Analytics — AI-Powered Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.51-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-1C3C3C?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![LangSmith](https://img.shields.io/badge/LangSmith-Observability-FF8C00?style=for-the-badge)](https://smith.langchain.com/)
[![SQLGlot](https://img.shields.io/badge/SQLGlot-AST_Security-2B3A42?style=for-the-badge)](https://github.com/tobymao/sqlglot)
[![Plotly](https://img.shields.io/badge/Plotly-Visualizations-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com/)
[![Pytest](https://img.shields.io/badge/Pytest-100%25_Passing-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://pytest.org)

An enterprise-grade, portfolio-quality analytics and conversational intelligence platform that synthesizes **12 years of longitudinal data (2005–2016)** across **1,247 higher education institutions**, **74 countries**, and **3 premier global ranking authorities**:
- **Times Higher Education (THE) World University Ranking**
- **Academic Ranking of World Universities (ARWU / Shanghai Ranking)**
- **Center for World University Rankings (CWUR)**

Built with a modern full-stack architecture featuring **PostgreSQL 18**, **FastAPI**, **LangGraph**, **LangSmith**, and **Streamlit**, this platform provides transparent, deterministic, and evidence-grounded insights into university performance, country distributions, criteria trade-offs, and student demographics.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Data Tier
        CSV["Raw Historical CSV Datasets"] --> INGEST["Idempotent Ingestion Pipeline"]
        INGEST --> PG[("PostgreSQL 18<br/>university_ranking_db")]
        PG --> RO_ROLE["ranking_readonly User Role"]
        PG --> VIEWS["v_ranked_universities & v_university_overview"]
    end

    subgraph Service Tier
        RO_ROLE --> ORM["SQLAlchemy Core & ORM Engine"]
        ORM --> SERVICES["Deterministic Analytics Services<br/>Overview • Comparison • Trends • Country • Criteria • Demographics"]
    end

    subgraph API Tier
        SERVICES --> FASTAPI["FastAPI REST Service<br/>OpenAPI Docs • Pydantic Schemas • Dependency Injection"]
    end

    subgraph GenAI Orchestration
        LLM_REQ["User Question"] --> LANGGRAPH["LangGraph Typed State Machine"]
        LANGGRAPH --> CLASSIFY["Intent Classifier & Router"]
        CLASSIFY --> SQL_GEN["SQL Generation<br/>Few-Shot Guidance & Acronym Expansion"]
        SQL_GEN --> AST_VAL["SQLGlot AST Safety Validator<br/>SELECT Only • Table Whitelist • Limit Enforcement"]
        AST_VAL --> RO_EXEC["PostgreSQL Read-Only Execution"]
        RO_EXEC --> ANSWER_GEN["Evidence-Based Grounded Answer Generator<br/>Context Window: 75 Rows"]
        ANSWER_GEN --> VIZ_REC["Adaptive Plotly Recommendation Engine"]
        LANGGRAPH -.-> TRACING["LangSmith Distributed Tracing & Latency Telemetry"]
    end

    subgraph Presentation Tier
        FASTAPI --> STREAMLIT["Streamlit Multi-Page Interactive Dashboard"]
        SERVICES -.-> STREAMLIT
        LANGGRAPH --> STREAMLIT
        STREAMLIT --> UI_PAGES["Executive Overview • University Benchmarking • Country Intelligence<br/>Historical Trends • Criteria Trade-offs • Demographics • AI Copilot"]
    end
```

---

## 🔬 Core Domain Principles & Methodological Integrity

Unlike naive analytics dashboards that blindly average disparate numbers, this platform adheres to strict data science and educational domain integrity:

### 1. Scale Isolation (Scores vs. Ranks)
- **Times Higher Education (THE):** Criteria 1–6 report normalized criteria scores ($0$ to $100$, where higher is better).
- **Shanghai Ranking (ARWU):** Criteria 7–13 report normalized criteria scores ($0$ to $100$, with right-skewed distributions reflecting elite institutional concentrations).
- **Center for World University Rankings (CWUR):** Criteria 14–20 report **ordinal ranking positions ($1$ to $1,000$, where lower is better)**. Criterion 21 (`Total CWUR`) is a compound score ($43$ to $100$).
- **Rule Enforced:** Cross-system composite averaging is strictly prohibited at both the database and UI layers. Ordinal rank metrics automatically invert their visualization Y-axes so upward visual momentum correctly denotes rising standing.

### 2. Demographic Scope & Associative Caution
- **Demographic Coverage:** Exactly 1,085 demographic records exist across 245 universities (2011–2016), matching the Times Higher Education survey coverage 1-to-1. Exactly 1,002 institutions have no recorded demographic data.
- **Associative Rule:** All demographic correlations (international student percentage, female student percentage, student-to-staff ratios) are explicitly presented as **associative patterns only**. The platform systematically rejects describing statistical correlation ($r$) as causal effect.

---

## 🛡️ Enterprise SQL Safety & Defense-in-Depth

The conversational AI assistant has strictly controlled, audited access to the PostgreSQL database:

1. **SQLGlot AST Parsing:** Every candidate query is parsed into an Abstract Syntax Tree (AST). Queries containing DDL (`DROP`, `ALTER`, `CREATE`), DML (`INSERT`, `UPDATE`, `DELETE`), multi-statement chaining (`;`), subquery injections, or database catalog probing (`pg_catalog`, `information_schema`) are rejected before execution.
2. **Schema & Table Allowlists:** Queries may only target 6 approved tables and 3 verified views: `university`, `country`, `ranking_system`, `ranking_criteria`, `university_ranking_year`, `university_year`, `v_university_overview`, `v_ranked_universities`, and `v_criteria_overview`.
3. **AST Limit Enforcement:** If a `SELECT` query lacks a `LIMIT` clause or specifies a limit greater than 100, the AST is automatically mutated to enforce `LIMIT 100`.
4. **Dedicated Read-Only Role:** Database connections execute under `ranking_readonly` with `GRANT SELECT ON ALL TABLES IN SCHEMA public`, ensuring write-protection at the PostgreSQL engine level.
5. **AST Statement Parameterization:** Safe identifier and literal binding eliminates raw string concatenation.
6. **5-Second Statement Timeout:** PostgreSQL statement timeouts prevent resource exhaustion or runaway queries.

---

## 🚀 Key Engineering Optimizations & Platform Hardening

### 1. Windows Python 3.13 C-Extension Deadlock Resolution
- Python 3.13 on Windows environments with Anaconda experiences thread deadlocks when importing heavy binary C-extensions like `orjson` and `ormsgpack`.
- Implemented drop-in compatibility shims in [`app.core.orjson_shim`](file:///c:/Users/pkatt/OneDrive/Desktop/Projects/University_Ranking_Analytics/university_ranking-main/app/core/orjson_shim.py) and [`app.core.ormsgpack_shim`](file:///c:/Users/pkatt/OneDrive/Desktop/Projects/University_Ranking_Analytics/university_ranking-main/app/core/ormsgpack_shim.py) registered directly into `sys.modules`.
- Fully declared all `OPT_*` flags (`OPT_SERIALIZE_NUMPY`, `OPT_NON_STR_KEYS`, `OPT_SORT_KEYS`, etc.) and configured `plotly.io.json.config.default_engine = "json"` for fast and seamless Plotly radar, choropleth, and line chart rendering.
- Replaced heavyweight `statsmodels` OLS imports with pure-NumPy linear regression (`np.polyfit`) for instant trendline calculation without native DLL conflicts.

### 2. OpenAI Transport Layer: Brotli C-Extension Compatibility
- In Python 3.13, Anaconda's `brotlicffi` package raises `TypeError: Decompressor.decompress() got an unexpected keyword argument 'output_buffer_limit'` when the OpenAI API server returns Brotli-compressed responses (`Accept-Encoding: br`).
- In [`app.llm.client`](file:///c:/Users/pkatt/OneDrive/Desktop/Projects/University_Ranking_Analytics/university_ranking-main/app/llm/client.py), injected a custom `httpx.Client(headers={"Accept-Encoding": "gzip, deflate"}, timeout=30.0)`. This completely bypasses the broken Brotli C-decoder and guarantees reliable, high-speed live LLM completions via `gpt-4o-mini`.

### 3. Schema Grounding, Acronym Expansion & Context Window Tuning
- **Few-Shot SQL Prompts:** Injected canonical examples into `SYSTEM_SQL_PROMPT` to guide the model on column naming (`v.year`, `v.score`, `v.university_name`), eliminating invalid compound identifiers.
- **Partial Matching & Acronym Expansion:** Implemented explicit rules mapping common abbreviations (e.g. `'MIT'` -> `'Massachusetts Institute of Technology'`, `'Caltech'` -> `'California Institute of Technology'`) with wildcard partial matching (`ILIKE '%...%'`).
- **Context Expansion for Multi-Entity Queries:** Expanded SQL results passed to the LLM from 15 to 75 rows in `generate_answer_node`. Head-to-head comparisons (such as Harvard vs. MIT vs. Stanford across all criteria) now receive and display the full dataset across all three institutions.
- **Dual Column Aliases in PostgreSQL:** Created `v_ranked_universities` with both `system_id` & `ranking_system_id` and `criteria_id` & `ranking_criteria_id` so generated SQL queries succeed regardless of which naming convention is chosen by the model.

### 4. High-Throughput REST Catalog & Responsive Frontend
- Increased pagination ceiling on `GET /universities` to `le=5000` in [`catalog.py`](file:///c:/Users/pkatt/OneDrive/Desktop/Projects/University_Ranking_Analytics/university_ranking-main/app/api/endpoints/catalog.py), allowing `GET /universities?limit=1500` to return all 1,247 universities with HTTP 200 in **~15 ms**.
- Aligned `GET /analytics/criteria?system_id={id}` to return both distribution summary statistics and pairwise Pearson correlation matrices in a single call.
- Enabled `show_spinner=False` on Streamlit `@st.cache_data` decorators in [`api_client.py`](file:///c:/Users/pkatt/OneDrive/Desktop/Projects/University_Ranking_Analytics/university_ranking-main/frontend/components/api_client.py) to prevent intrusive UI status banners during cache hydration.

---

## 📊 Analytics Services Capabilities

| Analytical Dimension | Capabilities & Domain Metrics | Visualization Suite |
| :--- | :--- | :--- |
| **Executive Overview** | Macro KPIs, institutional footprint, global coverage, triple-system institutions ($220$ universities). | Global Choropleth Map, Treemap of contributing nations, coverage bars, exportable CSV directory. |
| **University Benchmarking** | Multi-university side-by-side comparison across criteria and demographics. | Dynamic Radar / Spider polygons, grouped bar charts, comparative demographic scorecards. |
| **Country Intelligence** | Institutional density by nation, national representation across ranking bodies. | Horizontal benchmarking bar charts, global distribution maps, national institutional catalogs. |
| **Longitudinal Trends** | 12-year longitudinal trajectories (2005–2016) with scale-aware Y-axis, Top Movers & Decliners. | Multi-series line charts with inverted Y-axes for ranks, positive/negative momentum tables. |
| **Criteria Dynamics** | Inter-criteria distributions, dispersion metrics, statistical trade-offs. | Dimension score distributions, standard deviation variability charts, correlation matrices. |
| **Student Demographics** | Enrollment scale, staff-to-student ratios, gender parity, internationalization patterns. | Scatter plots with pure-NumPy regression trendlines, box plots by nation, demographic registry. |
| **AI Analytics Copilot** | Natural language queries, intent classification, schema-grounded SQL, AST validation. | Collapsible SQL inspection pills, underlying query record viewers, auto-rendered Plotly figures. |

---

## 🔍 LangSmith Observability & Evaluation Benchmark Suite

The platform integrates deep telemetry via LangSmith tracing (`@traceable`) with zero latency overhead:

- **End-to-End Node Tracing:** Traces `intake_and_classify`, `generate_sql`, `validate_sql`, `execute_query`, `generate_answer`, and `recommend_visualization`.
- **Latency Monitoring:** Automated tracking of total workflow runtime (`execution_time_ms`) with strict SLA boundary validation.
- **Evaluation Benchmark Suite (`tests/test_evaluations.py`):**
  1. `test_eval_highest_research_scores`: Factual retrieval accuracy and schema grounding.
  2. `test_eval_university_comparison`: Multi-entity retrieval across Harvard, MIT, and Stanford.
  3. `test_eval_country_representation`: Aggregation query accurately identifying USA ($273$ universities).
  4. `test_eval_system_methodology_routing`: Explanatory queries routed without unnecessary SQL synthesis.
  5. `test_eval_sql_injection_defense`: Multi-statement, DDL, and sleep attacks 100% blocked.
  6. `test_eval_groundedness_non_hallucination_empty_data`: Honest limitation reporting on absent years (e.g. 1980).
  7. `test_eval_latency_monitoring`: Validates execution time compliance under SLA thresholds.

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- **Python:** 3.11+ (Tested and verified on Python 3.13)
- **PostgreSQL:** 16+ (Running locally on port 5432)
- **Git**

### 2. Environment Setup
Clone the repository and install dependencies:

```bash
git clone https://github.com/pandukatti2000/University_Ranking_Analytics.git
cd University_Ranking_Analytics

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Local Configuration (`.env`)
Copy the template configuration file:

```bash
cp .env.example .env
```

Populate `.env` with your local PostgreSQL credentials and API keys:

```env
# Database Settings
DATABASE_URL=postgresql://postgres:YourPassword@127.0.0.1:5432/university_ranking_db
READONLY_DATABASE_URL=postgresql://ranking_readonly:readonly_password@127.0.0.1:5432/university_ranking_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YourPassword
POSTGRES_DB=university_ranking_db
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432

# OpenAI Settings
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# LangSmith Observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=university-ranking-analytics
```

### 4. Database Initialization & Data Ingestion
Execute the idempotent schema initialization and data ingestion scripts:

```bash
# 1. Initialize schema, views, and read-only security role
python scripts/setup_database.py

# 2. Ingest CSV datasets and reconcile row counts
python scripts/ingest_data.py
```

### 5. Running the Application

#### Start the FastAPI Backend:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Interactive Swagger documentation available at: `http://127.0.0.1:8000/docs`*

#### Start the Streamlit Analytics Dashboard:
```bash
streamlit run frontend/app.py
```
*Dashboard available at: `http://localhost:8501`*

---

## 🧪 Verification & Automated Test Suite

Run the full automated test suite covering all 6 tiers:

```bash
python -u run_tests.py
```

### Test Coverage Summary:
```text
tests/test_database.py     7 passed (100%) - Connection, row counts, null distributions, FKs, views, readonly security
tests/test_analytics.py    7 passed (100%) - KPIs, multi-system overlap, scale isolation, trends, criteria, demographics
tests/test_api.py         16 passed (100%) - Catalog, detail endpoints, comparative analytics, chat endpoints
tests/test_agent.py        7 passed (100%) - SQL safety, DDL/DML rejection, LangGraph state routing, read-only execution
tests/test_evaluations.py  7 passed (100%) - Factual accuracy, multi-entity comparison, injection defense, latency SLA
tests/test_frontend.py     3 passed (100%) - API client fallbacks, Plotly chart generators, view module imports
========================================================================================================================
Total:                    47 passed (100% pass rate)
```

### End-to-End Smoke Test:
Run the consolidated smoke test script:

```bash
python -u scripts/e2e_smoke_test.py
```

Output:
```text
======================================================================
SMOKE TEST SUMMARY RESULTS (Completed in 7.65s)
======================================================================
  [PASS]   PostgreSQL Database & Row Counts       : PASSED
  [PASS]   Read-Only Role Enforcement             : PASSED
  [PASS]   Analytics Services Engine              : PASSED
  [PASS]   FastAPI Endpoints                      : PASSED
  [PASS]   LangGraph AI Copilot & SQL Safety      : PASSED
  [PASS]   Streamlit Frontend & Plotly Suite      : PASSED
======================================================================
ALL SYSTEMS OPERATIONAL: End-to-End Platform is Healthy & Verified!
```

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status and PostgreSQL connectivity |
| `GET` | `/overview` | Top-level catalog KPIs, system coverage, and top countries |
| `GET` | `/overview/multi-system` | Institutions appearing across multiple ranking authorities |
| `GET` | `/universities` | Filterable and paginated directory of institutions (`limit` up to 5000) |
| `GET` | `/universities/{id}` | Detailed institutional profile and multi-system coverage |
| `GET` | `/countries` | Catalog of all 74 surveyed sovereign nations |
| `GET` | `/countries/{id}` | National profile, system representation, and institutional list |
| `GET` | `/ranking-systems` | Complete metadata on THE, ARWU, and CWUR ranking systems |
| `GET` | `/criteria` | Complete catalog of 21 criteria with metric types (score vs. rank) |
| `GET` | `/analytics/compare` | Head-to-head multi-university comparison with scale isolation |
| `GET` | `/analytics/trends` | Multi-year historical trajectories and Top Movers analysis |
| `GET` | `/analytics/criteria` | Statistical distributions, score dispersion, and pairwise Pearson correlations |
| `GET` | `/analytics/demographics` | Demographics overview, distributions, and non-causal correlations |
| `POST` | `/analytics/analyze` | Unified analytics dispatcher for structured reporting |
| `POST` | `/conversations/chat` | Natural language conversational AI endpoint powered by LangGraph |

---

## 🔒 Security & Privacy Commitments

- **No Hardcoded Secrets:** Credentials and API keys are strictly loaded via `.env` and kept out of version control via `.gitignore`.
- **Database Hardening:** The conversational agent operates exclusively through the `ranking_readonly` role.
- **SQL AST Validation:** SQL queries generated by LLMs are sanitized and AST-validated via SQLGlot before database execution.
- **Trace Scrubbing:** Sensitive authorization tokens and connection parameters are masked prior to LangSmith transmission.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
