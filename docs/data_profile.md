# University Ranking Analytics — Comprehensive Data Profile

## 1. Executive Summary

This profile provides an exhaustive technical analysis of the University Ranking dataset located at `university_ranking-main/university_ranking-main/Data`. The dataset consolidates multi-year institutional rankings and demographics across three prominent global higher education ranking systems:
1. **Times Higher Education (THE) World University Rankings** (2011–2016)
2. **Academic Ranking of World Universities (Shanghai / ARWU)** (2005–2015)
3. **Center for World University Rankings (CWUR)** (2012–2015)

The profiling confirms high relational integrity among the primary entities, but highlights critical domain, methodology, scale, and demographic coverage differences that dictate application architecture, analytical services, and LLM text-to-SQL logic.

---

## 2. File-by-File Technical Profile

| File Name | File Size | Row Count (excl. Header) | Column Count | Primary / Candidate Key | Foreign Keys | Missing Values | Encoding |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `country.csv` | 876 B | 74 | 2 | `id` | None | None | UTF-8 |
| `ranking_system.csv` | 123 B | 3 | 2 | `id` | None | None | UTF-8 |
| `ranking_criteria.csv` | 386 B | 21 | 3 | `id` | `ranking_system_id` &rarr; `ranking_system(id)` | None | UTF-8 |
| `university.csv` | 44.18 KB | 1,247 | 3 | `id` | `country_id` &rarr; `country(id)` | None | UTF-8 (110 rows contain non-ASCII chars) |
| `university_ranking_year.csv` | 497.47 KB | 29,612 | 4 | `(university_id, ranking_criteria_id, year)` | `university_id` &rarr; `university(id)`, `ranking_criteria_id` &rarr; `ranking_criteria(id)` | 130 null scores in criterion 5 (`Income`) | UTF-8 |
| `university_year.csv` | 29.28 KB | 1,085 | 6 | `(university_id, year)` | `university_id` &rarr; `university(id)` | 96 nulls in `pct_female_students` | UTF-8 |

---

## 3. High-Level Entity Counts & Coverage

- **Total Countries:** 74
- **Total Ranking Systems:** 3
- **Total Ranking Criteria:** 21
- **Total Registered Universities:** 1,247
- **Universities with at least one Ranking Record:** 1,065 (85.4% of registered)
- **Universities with No Ranking Records:** 182 (14.6% of registered; entity resolution variants from source scrape)
- **Overall Year Coverage:** 2005 – 2016 (12 years span)

### Cross-System University Representation
- **Universities in All 3 Systems:** 75 institutions (e.g., Harvard, MIT, Cambridge, Oxford, Stanford, Tokyo, Toronto)
- **Universities in THE & Shanghai:** 84
- **Universities in THE & CWUR:** 204
- **Universities in Shanghai & CWUR:** 84
- **Universities ONLY in CWUR:** 811
- **Universities ONLY in THE:** 32
- **Universities ONLY in Shanghai:** 0 (all 93 Shanghai universities appear in CWUR or THE)

---

## 4. Ranking System & Criteria Breakdown

### System 1: Times Higher Education (THE) World University Ranking
- **System ID:** 1
- **Temporal Coverage:** 2011 – 2016 (6 years)
- **Institutions Covered:** 245 unique institutions
- **Annual Coverage:**
  - 2011: 185 institutions
  - 2012: 196 institutions
  - 2013: 197 institutions
  - 2014: 198 institutions
  - 2015: 199 institutions
  - 2016: 110 institutions *(Note: significant reduction in 2016 records)*
- **Criteria Definitions & Distributions:**

| ID | Criteria Name | Metric Type | Record Count | Missing | Min | Max | Mean | Description & Scale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `Teaching` | Score | 1,085 | 0 | 16.0 | 100.0 | 51.4 | Learning environment (0–100 scale, higher is better) |
| 2 | `International` | Score | 1,085 | 0 | 15.0 | 100.0 | 58.9 | International staff, students & research (0–100 scale) |
| 3 | `Research` | Score | 1,085 | 0 | 13.0 | 99.0 | 52.9 | Volume, income and reputation (0–100 scale) |
| 4 | `Citations` | Score | 1,085 | 0 | 19.0 | 100.0 | 76.8 | Research influence (0–100 scale) |
| 5 | `Income` | Score | 955 | 130 | 24.0 | 100.0 | 54.1 | Industry income & knowledge transfer (0–100 scale) |
| 6 | `Total Times` | Score | 1,085 | 0 | 41.0 | 96.0 | 60.1 | Weighted composite score calculated by THE |

---

### System 2: Shanghai Ranking (ARWU - Academic Ranking of World Universities)
- **System ID:** 2
- **Temporal Coverage:** 2005 – 2015 (11 years)
- **Institutions Covered:** 93 unique elite research institutions
- **Annual Coverage:** 70 to 74 institutions per year (2005: 71, 2006: 71, 2007: 73, 2008: 72, 2009: 71, 2010: 72, 2011: 71, 2012: 71, 2013: 70, 2014: 70, 2015: 74)
- **Criteria Definitions & Distributions:**

| ID | Criteria Name | Metric Type | Record Count | Missing | Min | Max | Mean | Description & Scale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 7 | `Alumni` | Score | 786 | 0 | 0.0 | 100.0 | 25.4 | Alumni winning Nobel Prizes and Fields Medals |
| 8 | `Award` | Score | 786 | 0 | 0.0 | 100.0 | 27.9 | Staff winning Nobel Prizes and Fields Medals |
| 9 | `HiCi` | Score | 786 | 0 | 6.0 | 100.0 | 36.6 | Highly Cited Researchers |
| 10 | `N and S` | Score | 786 | 0 | 11.0 | 100.0 | 33.3 | Papers published in Nature and Science |
| 11 | `Pub` | Score | 786 | 0 | 19.0 | 100.0 | 54.0 | Papers indexed in Science/Social Science Citation Index |
| 12 | `PCP` | Score | 786 | 0 | 17.0 | 100.0 | 32.7 | Per capita academic performance of an institution |
| 13 | `Total Shanghai`| Score | 786 | 0 | 24.0 | 100.0 | 37.2 | ARWU composite score benchmarked to top university = 100 |

*Analytical Note:* Shanghai criteria reflect absolute research output and prize counts. Most institutions have 0 or very low scores in `Alumni` and `Award`, causing severe positive skewness (mean Total Shanghai is only 37.2).

---

### System 3: Center for World University Rankings (CWUR)
- **System ID:** 3
- **Temporal Coverage:** 2012 – 2015 (4 years)
- **Institutions Covered:** 1,024 unique institutions
- **Annual Coverage:**
  - 2012: 100 institutions
  - 2013: 100 institutions
  - 2014: 1,000 institutions *(Massive 10x expansion)*
  - 2015: 1,000 institutions
- **Criteria Definitions & Distributions:**

| ID | Criteria Name | Metric Type | Record Count | Missing | Min | Max | Mean | Description & Scale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 14 | `Quality of Education Rank` | **Rank** | 2,200 | 0 | 1 | 367 | 275.1 | Global rank (1 is best; lower is better) |
| 15 | `Alumni Employment Rank` | **Rank** | 2,200 | 0 | 1 | 567 | 357.1 | Global rank (1 is best; lower is better) |
| 16 | `Quality of Faculty Rank` | **Rank** | 2,200 | 0 | 1 | 218 | 178.9 | Global rank (1 is best; lower is better) |
| 17 | `Publications Rank` | **Rank** | 2,200 | 0 | 1 | 1,000 | 459.9 | Global rank (1 is best; lower is better) |
| 18 | `Influence Rank` | **Rank** | 2,200 | 0 | 1 | 991 | 459.8 | Global rank (1 is best; lower is better) |
| 19 | `Citations Rank` | **Rank** | 2,200 | 0 | 1 | 812 | 413.4 | Global rank (1 is best; lower is better) |
| 20 | `Patents Rank` | **Rank** | 2,200 | 0 | 1 | 871 | 433.3 | Global rank (1 is best; lower is better) |
| 21 | `Total CWUR` | **Score** | 2,200 | 0 | 43.0 | 100.0 | 47.8 | CWUR Composite score (0–100 scale, higher is better) |

---

## 5. Critical Methodology & Cross-System Distinctions

### Ranks vs. Scores
1. **CWUR Criteria 14–20 are Ranks:** Values range from 1 to 1,000. In these criteria, **lower numbers denote superior performance** (1 = world #1).
2. **CWUR Criterion 21 (`Total CWUR`) is a Score:** Values range from 43.0 to 100.0. Here, **higher numbers denote superior performance**.
3. **THE (1–6) and Shanghai (7–13) are entirely Scores:** All are 0–100 scales where higher is better.
4. **No Explicit Overall World Rank Column:** None of the tables contain a precomputed official integer `world_rank` column. Overall ranks must be computed deterministically via window functions:
   ```sql
   DENSE_RANK() OVER (PARTITION BY ranking_criteria_id, year ORDER BY score DESC)
   ```
   for composite scores (`Total Times`, `Total Shanghai`, `Total CWUR`).

### Comparability Across Systems
- Scores **CANNOT** be combined or directly compared across systems without transformation.
- A score of 70 in THE (`Total Times`) represents an elite global institution (~top 50).
- A score of 70 in Shanghai (`Total Shanghai`) represents an ultra-elite top-5 global institution (Harvard/Stanford tier).
- A score of 70 in CWUR represents a top 20 institution globally.
- CWUR's rank-based criteria cannot be averaged or correlated with percentage scores without rank inversion.

---

## 6. University Demographics Profile (`university_year`)

The `university_year` table provides institutional characteristics across 1,085 records.

### Coverage Findings
- **Institutions Covered:** 245 universities (exactly matching the 245 THE universities).
- **Years Covered:** 2011 to 2016.
- **Pair Matching:** There is a 100% exact match between `(university_id, year)` pairs in `university_year` and THE ranking entries.
- **Coverage Gap:** 1,002 universities in `university.csv` (80.4%) have **zero** demographic records. Demographics are unavailable for institutions appearing solely in CWUR or Shanghai.

### Demographic Attributes & Distributions

| Attribute | Data Type | Non-Null Count | Null Count (% Missing) | Min | Max | Mean | Median | Scale / Unit |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `num_students` | Integer | 1,085 | 0 (0.0%) | 462 | 127,431 | 24,010 | 20,950 | Headcount |
| `student_staff_ratio` | Decimal | 1,085 | 0 (0.0%) | 3.6 | 70.4 | 15.7 | 14.1 | Students per faculty member |
| `pct_international_students` | Integer | 1,085 | 0 (0.0%) | 1 | 54 | 19.7 | 18.0 | Percentage (0–100 scale) |
| `pct_female_students` | Decimal/Int | 989 | 96 (8.8%) | 13.0 | 70.0 | 49.4 | 51.0 | Percentage (0–100 scale) |

### Empirical Demographic Correlations (with THE Metrics)
- **`pct_international_students` vs. THE International Score (N=1,085):** $r = +0.786$ (Strong positive correlation)
- **`student_staff_ratio` vs. THE Teaching Score (N=1,085):** $r = -0.311$ (Moderate negative correlation; fewer students per faculty associates with higher teaching score)
- **`pct_female_students` vs. THE Total Score (N=989):** $r = -0.145$ (Slight negative correlation)
- **`num_students` vs. THE Research Score (N=1,085):** $r = +0.154$ (Weak positive correlation)

*(Note: In accordance with analytics standards, these correlations indicate associative patterns and must not be asserted as causal effects.)*

---

## 7. Data Quality, Integrity & Anomaly Assessment

1. **Referential Integrity: 100% Valid**
   - Zero orphaned records across all tables.
   - All foreign keys (`country_id`, `ranking_system_id`, `ranking_criteria_id`, `university_id`) resolve correctly.
2. **Duplication: 0 Duplicate Records**
   - Candidate keys `(university_id, ranking_criteria_id, year)` and `(university_id, year)` are strictly unique.
3. **Missing Value Hotspots:**
   - `university_ranking_year.score`: Exactly 130 null entries, strictly isolated to Criterion ID 5 (`Income`). All other 29,482 records are populated.
   - `university_year.pct_female_students`: Exactly 96 missing values (8.8%).
4. **The 182 Unranked Universities:**
   - `university.csv` contains 1,247 universities, but only 1,065 appear in `university_ranking_year`.
   - Inspection shows these 182 entries are name variants resulting from multi-source scraping (e.g., ID 1031 "University of Wisconsin" vs. ID 25 "University of Wisconsin–Madison"; ID 1043 "London School of Economics and Political Science" vs. ID 22 "London School of Economics").
   - These 182 records should be retained in the database for referential transparency, with clear UI/API indicators stating "No ranking records available".
5. **Database DDL Type Pitfall (MySQL vs. PostgreSQL):**
   - The original MySQL DDL typed `score` in `university_ranking_year` as `INT`, which would silently truncate decimal precision (e.g., 98.6 &rarr; 98).
   - In PostgreSQL, `score` must be defined as `NUMERIC(6,2)` or `DOUBLE PRECISION`.
   - In `university_year`, `pct_female_students` must be `NUMERIC(5,2)` to accept decimal values like `33.0`.
6. **Character Encoding:**
   - Files are encoded in UTF-8. 110 university names include non-ASCII characters (e.g., en-dash `–`, umlauts `ü`, accents `é`, tildes `ã`). The PostgreSQL database must be initialized with `ENCODING = 'UTF8'` and `LC_COLLATE = 'C'` or `en_US.UTF-8`.
