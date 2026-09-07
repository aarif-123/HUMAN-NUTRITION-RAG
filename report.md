# 🥗 Nutri-RAG Evaluation Report

**Timestamp:** `2026-09-07T01:37:37.463786+00:00`

## 📊 Executive Summary

| Metric | Value |
|---|---|
| **Total Samples** | `5` |
| **Pass Rate** | **`100.0%`** (`5/5`) |
| **Mean Overall Score** | **`98.8%`** |
| **Mean Faithfulness (Groundedness)** | `90.0%` |
| **Mean Context Relevance** | `57.8%` |
| **Mean Answer Relevance** | `77.4%` |
| **Mean Citation Accuracy** | `99.6%` |

## 🧪 Detailed Results Breakdown

### 1. `NUTRITION_001_VITAMIN_C_COLLAGEN` — ✅ **PASS**

- **Query:** *"What is the role of Vitamin C in collagen synthesis?"*
- **Overall Score:** `97.6%`
- **Execution Time:** `27.77s`

| Dimension | Score | Threshold | Passed | Justification |
|---|---|---|---|---|
| **Faithfulness** | `100.0%` | `85%` | Yes | All extracted claims are explicitly supported by the provided research context. |
| **Context Relevance** | `96.0%` | `70%` | Yes | Both retrieved chunks directly explain Vitamin C's role as a cofactor for prolyl and lysyl hydroxylases in collagen synthesis and describe the consequences of its deficiency, providing essential and focused information to answer the query. |
| **Answer Relevance** | `95.0%` | `80%` | Yes | The response directly addresses the query by explaining Vitamin C's role as a cofactor for prolyl and lysyl hydroxylases, its importance for hydroxylation and triple-helix stability in collagen, and mentions the consequence of deficiency (scurvy). It is concise and stays on topic without unnecessary information. |
| **Citation Accuracy** | `98.1%` | `80%` | Yes | Valid citations across 3/4 statements. Bounds validity: 100%, Content overlap: 64%. |

---

### 2. `NUTRITION_002_VITAMIN_D_CALCIUM` — ✅ **PASS**

- **Query:** *"How does active Vitamin D regulate calcium absorption in the intestine?"*
- **Overall Score:** `98.4%`
- **Execution Time:** `20.15s`

| Dimension | Score | Threshold | Passed | Justification |
|---|---|---|---|---|
| **Faithfulness** | `100.0%` | `85%` | Yes | All four extracted claims are explicitly stated or directly inferred from the provided research context; no contradictions or unsupported statements were found. |
| **Context Relevance** | `97.0%` | `70%` | Yes | The chunk directly explains that active Vitamin D (calcitriol) binds VDR in enterocytes and upregulates calbindin-D9k, TRPV6, and PMCA1b, which together increase intestinal calcium absorption. This is precisely the mechanism asked for, with minimal extraneous information. |
| **Answer Relevance** | `96.0%` | `80%` | Yes | The response directly addresses how active Vitamin D (calcitriol) regulates intestinal calcium absorption by describing VDR binding, upregulation of specific transport proteins (calbindin-D9k, TRPV6, PMCA1b), and the resulting increase in transcellular calcium transport. It is concise, complete, and contains no irrelevant information. |
| **Citation Accuracy** | `100.0%` | `80%` | Yes | Valid citations across 4/4 statements. Bounds validity: 100%, Content overlap: 52%. |

---

### 3. `NUTRITION_003_IRON_INHIBITORS` — ✅ **PASS**

- **Query:** *"What dietary compounds inhibit non-heme iron absorption?"*
- **Overall Score:** `98.2%`
- **Execution Time:** `10.22s`

| Dimension | Score | Threshold | Passed | Justification |
|---|---|---|---|---|
| **Faithfulness** | `100.0%` | `85%` | Yes | All three extracted atomic claims are explicitly present in the provided research context; none are contradicted or unsupported. |
| **Context Relevance** | `96.0%` | `70%` | Yes | The retrieved chunk directly lists dietary compounds (phytates, polyphenols/tannins, excess calcium) that inhibit non-heme iron absorption, fully addressing the user query with minimal extraneous information. |
| **Answer Relevance** | `96.0%` | `80%` | Yes | The response directly lists the dietary compounds that inhibit non‑heme iron absorption—phytates, polyphenols/tannins, and calcium—matching the query precisely and concisely without extraneous information. |
| **Citation Accuracy** | `100.0%` | `80%` | Yes | Valid citations across 4/4 statements. Bounds validity: 100%, Content overlap: 82%. |

---

### 4. `CONVERSATION_001_GREETING` — ✅ **PASS**

- **Query:** *"Hello! Can you introduce yourself?"*
- **Overall Score:** `100.0%`
- **Execution Time:** `9.82s`

| Dimension | Score | Threshold | Passed | Justification |
|---|---|---|---|---|
| **Faithfulness** | `50.0%` | `85%` | **No** | No context chunks provided for claim verification. |
| **Context Relevance** | `0.0%` | `70%` | **No** | No chunks were retrieved from the vector database. |
| **Answer Relevance** | `100.0%` | `80%` | Yes | The response directly answers the user's request for an introduction by providing a clear greeting and a concise self-introduction, fully satisfying the query without irrelevant content. |
| **Citation Accuracy** | `100.0%` | `80%` | Yes | No context chunks provided; response correctly contained no citations. |

---

### 5. `FALLBACK_001_UNGROUNDED_QUERY` — ✅ **PASS**

- **Query:** *"What is the latest quantum computing algorithm for Shor's factorization?"*
- **Overall Score:** `100.0%`
- **Execution Time:** `1.42s`

| Dimension | Score | Threshold | Passed | Justification |
|---|---|---|---|---|
| **Faithfulness** | `100.0%` | `85%` | Yes | No context chunks provided for claim verification. |
| **Context Relevance** | `0.0%` | `70%` | **No** | No chunks were retrieved from the vector database. |
| **Answer Relevance** | `0.0%` | `80%` | **No** | The generated response does not address the user's query about the latest quantum computing algorithm for Shor's factorization. Instead, it incorrectly redirects to nutrition topics, providing no relevant information. |
| **Citation Accuracy** | `100.0%` | `80%` | Yes | No context chunks provided; response correctly contained no citations. |
| **Refusal Adherence** | `100.0%` | `80%` | Yes | The assistant correctly identified the lack of sufficient context, politely declined to provide an answer, and did not fabricate any ungrounded scientific facts. |

---
