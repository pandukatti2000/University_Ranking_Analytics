# University Ranking Analytics — Data Dictionary

## 1. Relational Schema Architecture

The platform's PostgreSQL database schema consists of six core entities arranged in a normalized relational structure:

```
country (id)
   ▲
   │ (1:N)
   │
university (id) ◄──────┐
   ▲                   │ (1:N)
   │ (1:N)             │
university_year   university_ranking_year
(university_id,        ▲
 year)                 │ (N:1)
                       │
                 ranking_criteria (id)
                       ▲
                       │ (N:1)
                       │
                 ranking_system (id)
```

---

## 2. Table-by-Table Data Dictionary

### Table 1: `country`
Contains standardized global country names and identifiers.

- **Primary Key:** `id`
- **Total Records:** 74

| Column Name | PostgreSQL Type | Nullable | Key | Constraints / Default | Description & Sample |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | NO | PK | Auto-increment / Identity | Unique country identifier (e.g., `1`, `73`) |
| `country_name` | `VARCHAR(100)` | NO | None | Unique constraint recommended | Full English country name (e.g., `United States of America`, `United Kingdom`, `Japan`) |

---

### Table 2: `ranking_system`
Catalog of the three world university ranking systems represented in the dataset.

- **Primary Key:** `id`
- **Total Records:** 3

| Column Name | PostgreSQL Type | Nullable | Key | Constraints / Default | Description & Sample |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | NO | PK | Auto-increment / Identity | Unique system identifier (`1`, `2`, `3`) |
| `system_name` | `VARCHAR(100)` | NO | None | Unique | Full name of ranking authority (e.g., `Times Higher Education World University Ranking`) |

#### Record Mapping:
- `1`: **Times Higher Education World University Ranking** (THE)
- `2`: **Shanghai Ranking** (Academic Ranking of World Universities / ARWU)
- `3`: **Center for World University Rankings** (CWUR)

---

### Table 3: `ranking_criteria`
Enumeration of the 21 evaluated dimensions across the three ranking systems.

- **Primary Key:** `id`
- **Foreign Key:** `ranking_system_id` &rarr; `ranking_system(id)`
- **Total Records:** 21

| Column Name | PostgreSQL Type | Nullable | Key | Constraints / Default | Description & Sample |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | NO | PK | Auto-increment / Identity | Unique criteria identifier (`1` to `21`) |
| `ranking_system_id` | `INTEGER` | NO | FK | References `ranking_system(id)` ON DELETE RESTRICT | ID of the parent ranking system |
| `criteria_name` | `VARCHAR(200)` | NO | None | None | Official criterion name (e.g., `Teaching`, `Alumni`, `Quality of Education Rank`) |

---

### Table 4: `university`
Master registry of all higher education institutions.

- **Primary Key:** `id`
- **Foreign Key:** `country_id` &rarr; `country(id)`
- **Total Records:** 1,247 (1,065 ranked, 182 unranked)

| Column Name | PostgreSQL Type | Nullable | Key | Constraints / Default | Description & Sample |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | NO | PK | Auto-increment / Identity | Unique university identifier (`1` to `1247`) |
| `country_id` | `INTEGER` | NO | FK | References `country(id)` ON DELETE RESTRICT | Identifier of the country where institution is located |
| `university_name` | `VARCHAR(200)` | NO | None | Index recommended | Full institutional name, UTF-8 formatted (e.g., `Harvard University`, `École normale supérieure - Paris`) |

---

### Table 5: `university_ranking_year`
Fact table recording scores and ordinal ranks for an institution, criterion, and year.

- **Primary / Composite Key:** `(university_id, ranking_criteria_id, year)`
- **Foreign Keys:**
  - `university_id` &rarr; `university(id)`
  - `ranking_criteria_id` &rarr; `ranking_criteria(id)`
- **Total Records:** 29,612

| Column Name | PostgreSQL Type | Nullable | Key | Constraints / Default | Description & Sample |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `university_id` | `INTEGER` | NO | FK, PK-part | References `university(id)` ON DELETE CASCADE | University evaluated |
| `ranking_criteria_id` | `INTEGER` | NO | FK, PK-part | References `ranking_criteria(id)` ON DELETE CASCADE | Evaluated criterion |
| `year` | `SMALLINT` | NO | PK-part | `CHECK (year BETWEEN 2000 AND 2030)` | Evaluation publication year (`2005`–`2016`) |
| `score` | `NUMERIC(6,2)` | YES | None | None | Criterion value. 130 nulls in Criterion 5 (`Income`). Represents either a normalized score (0–100) or an ordinal rank (1–1000) depending on criterion. |

---

### Table 6: `university_year`
Demographic and operational profile of institutions over time.

- **Primary / Composite Key:** `(university_id, year)`
- **Foreign Key:** `university_id` &rarr; `university(id)`
- **Total Records:** 1,085 (Exclusively covers THE universities for 2011–2016)

| Column Name | PostgreSQL Type | Nullable | Key | Constraints / Default | Description & Sample |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `university_id` | `INTEGER` | NO | FK, PK-part | References `university(id)` ON DELETE CASCADE | Institution evaluated |
| `year` | `SMALLINT` | NO | PK-part | `CHECK (year BETWEEN 2000 AND 2030)` | Academic census year (`2011`–`2016`) |
| `num_students` | `INTEGER` | NO | None | `CHECK (num_students > 0)` | Total enrolled student body count (range: 462 to 127,431) |
| `student_staff_ratio` | `NUMERIC(5,2)` | NO | None | `CHECK (student_staff_ratio > 0)` | Full-time equivalent students per academic staff member (range: 3.6 to 70.4) |
| `pct_international_students` | `SMALLINT` | NO | None | `CHECK (pct_international_students BETWEEN 0 AND 100)` | Percentage of enrolled international students (range: 1 to 54) |
| `pct_female_students` | `NUMERIC(5,2)` | YES | None | `CHECK (pct_female_students BETWEEN 0 AND 100)` | Percentage of enrolled female students. 96 null records (8.8% missing). (range: 13.0 to 70.0) |

---

## 3. Exhaustive Criteria Master Catalog

The table below defines all 21 criteria, explicitly distinguishing metric nature, domain interpretation, and optimization direction.

| ID | System Name | Criteria Name | Metric Type | Value Range | Optimization Direction | Definition / Methodology |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **1** | Times Higher Education | `Teaching` | **Score** | 16.0 – 100.0 | Higher is Better | Learning environment: reputation survey (15%), staff-to-student ratio (4.5%), doctorate-to-bachelor's ratio (2.25%), doctorates-awarded-to-academic-staff (6%), institutional income (2.25%). |
| **2** | Times Higher Education | `International` | **Score** | 15.0 – 100.0 | Higher is Better | International outlook: proportion of international students (2.5%), international staff (2.5%), and international co-authorship (2.5%). |
| **3** | Times Higher Education | `Research` | **Score** | 13.0 – 99.0 | Higher is Better | Research volume, income, and reputation: reputation survey (18%), research income (6%), research productivity (6%). |
| **4** | Times Higher Education | `Citations` | **Score** | 19.0 – 100.0 | Higher is Better | Research influence: field-normalized citation impact per published paper (30% weight). |
| **5** | Times Higher Education | `Income` | **Score** | 24.0 – 100.0 | Higher is Better | Industry income and knowledge transfer: research income from industry per academic staff (2.5% weight). 130 null values in dataset. |
| **6** | Times Higher Education | `Total Times` | **Score** | 41.0 – 96.0 | Higher is Better | Weighted composite overall score computed by THE. |
| **7** | Shanghai Ranking (ARWU) | `Alumni` | **Score** | 0.0 – 100.0 | Higher is Better | Total number of alumni winning Nobel Prizes and Fields Medals (10% weight). |
| **8** | Shanghai Ranking (ARWU) | `Award` | **Score** | 0.0 – 100.0 | Higher is Better | Total number of staff winning Nobel Prizes and Fields Medals (20% weight). |
| **9** | Shanghai Ranking (ARWU) | `HiCi` | **Score** | 6.0 – 100.0 | Higher is Better | Number of Highly Cited Researchers selected by Clarivate (20% weight). |
| **10** | Shanghai Ranking (ARWU) | `N and S` | **Score** | 11.0 – 100.0 | Higher is Better | Papers published in Nature and Science over a 5-year window (20% weight). |
| **11** | Shanghai Ranking (ARWU) | `Pub` | **Score** | 19.0 – 100.0 | Higher is Better | Papers indexed in Science Citation Index-Expanded and Social Science Citation Index (20% weight). |
| **12** | Shanghai Ranking (ARWU) | `PCP` | **Score** | 17.0 – 100.0 | Higher is Better | Per capita academic performance: weighted score of the above divided by full-time academic staff (10% weight). |
| **13** | Shanghai Ranking (ARWU) | `Total Shanghai`| **Score** | 24.0 – 100.0 | Higher is Better | Overall composite ARWU score benchmarked to top-ranked university = 100.0. |
| **14** | CWUR | `Quality of Education Rank` | **Rank** | 1 – 367 | **Lower is Better** | World rank based on the number of university alumni who won major academic distinctions (25% weight in CWUR). |
| **15** | CWUR | `Alumni Employment Rank` | **Rank** | 1 – 567 | **Lower is Better** | World rank based on alumni holding CEO positions at world's top companies (25% weight). |
| **16** | CWUR | `Quality of Faculty Rank` | **Rank** | 1 – 218 | **Lower is Better** | World rank based on faculty members winning major international honors (25% weight). |
| **17** | CWUR | `Publications Rank` | **Rank** | 1 – 1,000 | **Lower is Better** | World rank based on total research papers in reputable journals (10% weight). |
| **18** | CWUR | `Influence Rank` | **Rank** | 1 – 991 | **Lower is Better** | World rank based on research papers appearing in highly influential journals (5% weight). |
| **19** | CWUR | `Citations Rank` | **Rank** | 1 – 812 | **Lower is Better** | World rank based on number of highly cited research papers (5% weight). |
| **20** | CWUR | `Patents Rank` | **Rank** | 1 – 871 | **Lower is Better** | World rank based on international patent filings (10% weight). |
| **21** | CWUR | `Total CWUR` | **Score** | 43.0 – 100.0 | Higher is Better | CWUR composite score benchmarked to top university = 100.0. |

---

## 4. Analytical & Text-to-SQL Operating Rules

When querying or analyzing this dataset (manually or via AI agents), the following deterministic rules must be enforced:

1. **Never conflate Ranks and Scores:**
   - Criteria 14–20 are ordinal ranks: `ORDER BY score ASC` indicates top performance.
   - Criteria 1–13 and 21 are scores: `ORDER BY score DESC` indicates top performance.
2. **Never aggregate scores across ranking systems:**
   - Do not perform `AVG(score)` across distinct `ranking_system_id` values.
   - Filter queries explicitly by `ranking_system_id` or `ranking_criteria_id`.
3. **Computing Overall University Ranks:**
   - To compute an institution's official rank in a system for a given year:
     - For THE: Rank universities by Criterion 6 (`Total Times`) descending.
     - For Shanghai: Rank universities by Criterion 13 (`Total Shanghai`) descending.
     - For CWUR: Rank universities by Criterion 21 (`Total CWUR`) descending.
4. **Demographic Coverage Boundaries:**
   - Demographics in `university_year` exist **only** for THE institutions (2011–2016).
   - Any query attempting to correlate demographics with CWUR or Shanghai scores must account for the inner join intersection (only institutions present in both).
5. **Handling Missing Values:**
   - Use `WHERE score IS NOT NULL` when computing statistics on Criterion 5 (`Income`).
   - Use `WHERE pct_female_students IS NOT NULL` when computing female student distributions.
   - Treat the 182 unranked institutions gracefully: they exist in `university` but have no entries in `university_ranking_year`.
