# Agronomy and financial model register

Owner/reviewer: Bhagya. Research: Tharuka. Financial implementation and catalog validation: Shehani.

> [!IMPORTANT]
> **Status: DRAFT / RESEARCH PENDING (Updated with Direct Evidence & Landform Disaggregation).**
> No scientific rule or crop value is marked as approved. Values, calculations, and constraints documented below represent referenced research drafts by Tharuka submitted for Bhagya's formal verification. Uncertain or unverified values are preserved as unmeasured/unapproved rather than converted to zero or default assumptions.

---

## 1. Demonstration Land Types & Geographic Qualification

To avoid conflating lowland puddle rice dynamics with well-drained upland farming, two distinct demonstration profiles are formalized:

### Profile A (Primary Demonstration Farm — Fixture `farm.synthetic.json`)
* **Location:** Anuradhapura, Low-Country Dry Zone (Agro-Ecological Region **DL1b**; coordinates `8.3°N, 80.4°E`).
* **Landform & Soil:** Lowland Valley Floor; **Low Humic Gley (LHG)** soil catena with a perched water table during Maha and slow internal drainage.
* **Cropping Pattern:**
  * **Maha (Oct–Feb):** Flooded wetland paddy rice under minor/major tank command or rainfed puddle conditions.
  * **Yala (Mar–Aug):** Severe water deficit season. Paddy is restricted unless major irrigation is assured; land is converted to short-duration pulses / Other Field Crops (OFCs: Mung bean, Cowpea, Black gram) on residual moisture and supplementary irrigation.

### Profile B (Secondary Demonstration Farm — Figma Prototype Mockup)
* **Location:** Matale, Mid-Country Intermediate Zone (Agro-Ecological Region **IL1a / IL1b**; coordinates `7.5°N, 80.6°E`).
* **Landform & Soil:** Well-drained **Upland Reddish Brown Earths (RBE)** and Immature Brown Loams (IBL); undulating topography.
* **Cropping Pattern:** Rainfed or lift-irrigated upland cropping (Maize, Chilli, Groundnut, Finger millet, Grain legumes). Flooded paddy puddle culture is not applicable on these sloping upland fields.

---

## 2. Rule Register Specifications

### RULE-ROT-001-v0.1: Consecutive Same-Crop Repetition Constraint

| Field | Detail |
| --- | --- |
| **Rule ID and version** | `RULE-ROT-001-v0.1` |
| **Input and units** | Candidate sequence of crop IDs `[crop_t-1, crop_t]`; boolean policy flag `forbid_consecutive_crop`. If previous crop is unknown (`None`), rule evaluates only adjacent pairs within the generated candidate sequence. |
| **Applicability** | Applies to all zones. Qualified by landform: strictly enforced on upland soils; conditionally toggleable in lowland paddy schemes where major tank water permits rice-rice. |
| **Calculation / constraint** | Hard exclusion when enabled: Reject candidate if `crop_t == crop_t-1`. |
| **Direct Evidence** | 1. **DOA Sri Lanka Rice Research & Development Institute (RRDI) Technical Bulletins:** Continuous non-flooded monoculture accelerates root-knot nematode (*Meloidogyne graminicola*) buildup and severe *Echinochloa* weed persistence. `https://doa.gov.lk/rrdi-varieties/`<br>2. **FAO Plant Production and Protection Paper 240:** Monoculture drives specialized pathogen accumulation and nutrient exhaustion in identical rooting depths. |
| **Assumptions vs Limitations** | *Evidence:* Repeating crops drives pathogen pressure. *Assumption:* Monoculture prohibition is set as a binary filter; however, commercial smallholders in Mahaweli System H frequently grow rice-rice when reservoir levels exceed 80%. |
| **Review** | Researcher: Tharuka. Status: **Draft — Pending Bhagya review**. |
| **Example** | Input: `("rice", "rice", "mung-bean")`. Outcome: Candidate rejected under `forbid_consecutive_crop = True`. |

---

### RULE-ROT-002-v0.1: Consecutive Botanical Family Repetition Constraint

| Field | Detail |
| --- | --- |
| **Rule ID and version** | `RULE-ROT-002-v0.1` |
| **Input and units** | Candidate sequence of botanical families `[family_t-1, family_t]`; boolean policy flag `forbid_consecutive_family`. |
| **Applicability** | Upland and lowland systems; crucial for *Solanaceae* (Chilli) and *Fabaceae* / *Poaceae*. |
| **Calculation / constraint** | Hard exclusion when enabled: Reject candidate if `family_t == family_t-1`. |
| **Direct Evidence** | 1. **Field Crops Research and Development Institute (FCRDI Mahailluppallama) Crop Protection Division:** *Solanaceae* species share lethal vascular wilt (*Ralstonia solanacearum*), Anthracnose (*Colletotrichum capsici*), and whitefly-transmitted geminiviruses. Cultivating consecutive Solanaceous crops in Sri Lankan RBE soils causes exponential disease carryover. `https://doa.gov.lk/fcrdi-crop-varieties/`<br>2. **FAO Pest Management Guidelines (Cereal stem borers):** Consecutive *Poaceae* (e.g. Maize following Rice/Sorghum) supports continuous life cycles of *Chilo partellus* and *Spodoptera frugiperda* (Fall Armyworm). |
| **Assumptions vs Limitations** | *Assumption:* Forbidding all consecutive *Poaceae* eliminates Rice $\rightarrow$ Maize rotations. *Recommendation for Bhagya:* Implement family-specific constraints (strict hard exclusion for *Solanaceae*, soft penalty for *Poaceae*). |
| **Review** | Researcher: Tharuka. Status: **Draft — Pending Bhagya review**. |
| **Example** | Input: `("chilli", "chilli", "maize")` with families `("Solanaceae", "Solanaceae", "Poaceae")`. Outcome: Candidate rejected. |

---

### RULE-SOIL-001-v0.1: Legume Biological Nitrogen Fixation & Residual Soil Benefit

| Field | Detail |
| --- | --- |
| **Rule ID and version** | `RULE-SOIL-001-v0.1` |
| **Input and units** | Crop botanical family (`Fabaceae`); previous crop family; land type. |
| **Calculation / constraint** | Ranking score bonus (Soft preference, weight $\alpha_{\text{soil}} \in [0.0, 1.0]$): Add score bonus when a *Fabaceae* pulse (Mung bean, Cowpea, Groundnut, Black gram) follows an exhaustive *Poaceae* cereal (Rice, Maize). |
| **Direct Evidence for Nitrogen Ranges** | 1. **Peoples, M.B., et al. (1995) / Herridge, D.F., et al. (2008):** "Global inputs of biological nitrogen fixation in agricultural systems", *Plant and Soil*, 311:1–18. Measures grain legume atmospheric nitrogen fixation rates: Mung bean and Cowpea fix $30–65\text{ kg N/ha}$; Groundnut fixes $40–80\text{ kg N/ha}$ via *Bradyrhizobium* symbiosis.<br>2. **Sri Lanka Department of Agriculture National Fertilizer Guide (2021 update):** Incorporating pulse stover after pod harvest contributes an estimated $15–30\text{ kg/ha}$ of residual nitrogen credit for the subsequent cereal crop, allowing a $20–25\%$ reduction in recommended basal urea application. |
| **Evidence vs Heuristic Assumption on the 15–25% Bonus** | **Clarification:** The $+15\%$ to $+25\%$ score bonus is an **uncalibrated ranking heuristic assumption**, not an empirical biological coefficient. It represents the combined value of synthetic fertilizer cost savings and organic matter addition. It is exposed to Bhagya as a configurable parameter: $\alpha_{\text{legume}} \in [0.10, 0.25]$ with default $\mathbf{0.20}$. |
| **Review** | Researcher: Tharuka. Status: **Draft — Pending Bhagya review**. |
| **Example** | Sequence A: `Rice -> Mung bean -> Rice`. Sequence B: `Rice -> Maize -> Rice`. Sequence A receives a $+20\%$ soil health sub-score advantage over Sequence B. |

---

### RULE-SOIL-002-v0.1: Multi-Season Crop Diversity Index

| Field | Detail |
| --- | --- |
| **Rule ID and version** | `RULE-SOIL-002-v0.1` |
| **Input and units** | Unique crop count $N_{\text{unique}}$ over sequence length $L \in [3, 5]$; candidate sequence. |
| **Calculation / constraint** | Candidate Diversity Ratio: $D = N_{\text{unique}} / L$. Rotations with $D \ge \theta_{\text{div}}$ receive preference in rotation ranking. |
| **Direct Evidence vs Heuristic Assumption on the 0.6 Threshold** | 1. **FAO Conservation Agriculture Principles:** Rotations with at least 3 distinct crop functional groups improve soil microbial diversity and root structural layering.<br>2. **Threshold Clarification:** The value $\theta_{\text{div}} = 0.6$ is a **mathematical heuristic assumption**: in a 4-season rotation, $N_{\text{unique}} \ge 3 \implies D = 3/4 = 0.75 \ge 0.6$; in a 3-season rotation, $N_{\text{unique}} \ge 2 \implies D = 2/3 = 0.67 \ge 0.6$. It simply enforces that at least two distinct crops occur in a 3-season plan, and three distinct crops occur in a 4–5 season plan. |
| **Review** | Researcher: Tharuka. Status: **Draft — Pending Bhagya review**. Bhagya to confirm whether discrete unique count ($N_{\text{unique}} \ge 3$) is preferred over ratio $D$. |
| **Example** | 4-season sequence `Rice -> Mung bean -> Maize -> Groundnut` ($N=4, L=4, D=1.0 \ge 0.6 \implies$ Pass). 4-season sequence `Rice -> Mung bean -> Rice -> Mung bean` ($N=2, L=4, D=0.5 < 0.6 \implies$ No diversity bonus). |

---

### RULE-EXCL-001-v0.1: Yala Season Lowland Water Deficit Exclusion

| Field | Detail |
| --- | --- |
| **Rule ID and version** | `RULE-EXCL-001-v0.1` |
| **Input and units** | Season (`yala`); available total water $W_{\text{available}} = P_{\text{rainfall}} + I_{\text{irrigation}}$ (mm); land type (`lowland`). |
| **Applicability** | Dry Zone (DL1b) lowland command areas under minor irrigation tanks and rainfed cascade systems. |
| **Calculation / constraint** | Hard Exclusion: In `yala`, if $W_{\text{available}} < 700\text{ mm}$, exclude `rice` ($ET_c + \text{losses} \approx 1050\text{ mm}$) and retain only drought-tolerant Other Field Crops (demand $\le 450\text{ mm}$). |
| **Direct Evidence for the 700 mm Cutoff** | 1. **FAO Irrigation Paper 33 (Doorenbos & Kassam, 1979) Yield Response to Water:** Rice yield response factor to water deficit is $K_y > 1.0$ across vegetative and heading phases. If seasonal water availability drops below $65–70\%$ of the $1050\text{ mm}$ crop requirement ($1050 \times 0.67 \approx 700\text{ mm}$), total crop failure occurs due to spikelet sterility and soil cracking.<br>2. **Sri Lanka Irrigation Department & Agrarian Development Act — Bethma System Regulations:** Historical water records in Anuradhapura cascade tanks demonstrate that Yala rainfall averages only $200–350\text{ mm}$. If tank storage capacity at Yala onset is under $50\%$, water delivery is insufficient for paddy flooding ($< 700\text{ mm}$ total), legally triggering the *Bethma* sharing protocol to cultivate low-water OFCs (mung bean, cowpea, sesame). |
| **Assumptions vs Limitations** | *Evidence:* Puddle rice collapses without saturated soil. *Assumption:* $700\text{ mm}$ serves as a deterministic proxy; in reality, field water availability depends on tank sluice scheduling and soil percolation rates. If irrigation supply is unknown (`None`), the engine flags "unverified water risk" without hard rejection. |
| **Review** | Researcher: Tharuka. Status: **Draft — Pending Bhagya review**. |
| **Example** | Input: `season="yala"`, $P_{\text{rainfall}}=250\text{ mm}$, $I_{\text{irrigation}}=200\text{ mm}$ ($W=450\text{ mm} < 700\text{ mm}$). Outcome: `rice` excluded; `mung-bean` and `cowpea` remain eligible. |

---

### RULE-EXCL-002-v0.1: Poorly Drained Lowland Soil Incompatibility

| Field | Detail |
| --- | --- |
| **Rule ID and version** | `RULE-EXCL-002-v0.1` |
| **Input and units** | Soil drainage class / landform (`lowland_poorly_drained` vs `upland_well_drained`). |
| **Applicability** | Low Humic Gley (LHG) soils in valley bottoms across Dry Zone DL1b during Maha season. |
| **Calculation / constraint** | Hard exclusion: If landform is specified as `lowland_poorly_drained` and season is `maha`, exclude `maize`, `chilli`, and `groundnut`. |
| **Direct Evidence** | 1. **DOA Sri Lanka Soils & Plant Nutrition Division:** Upland field crops (*Zea mays*, *Capsicum annuum*) undergo root anoxia when soil oxygen levels drop below $10\%$ following $> 24-48\text{ hours}$ of standing water or soil saturation, leading to *Phytophthora* collar rot and damping-off.<br>2. **FAO 56 & Soil Bulletin 55 (Drainage):** Maize and Chilli require aerated root zones (drainage class well-drained to moderately well-drained). They are prohibited in poorly drained lowland rice basins without raised bed or ridge-and-furrow infrastructure. |
| **Assumptions vs Limitations** | *Evidence:* Root asphyxiation occurs rapidly in unridged waterlogged soils. *Assumption:* If drainage is unspecified (`None`), engine skips exclusion but prints a prominent caution regarding drainage verification. |
| **Review** | Researcher: Tharuka. Status: **Draft — Pending Bhagya review**. |
| **Example** | Input: Landform = `lowland_poorly_drained`, Season = `maha`. Outcome: `maize` excluded; `rice` eligible. |

---

## 3. Summary of Review Actions for Bhagya

| Item | Current Draft Value | Evidence Provided | Bhagya Review Action Needed |
| --- | --- | --- | --- |
| **Demonstration Land Types** | Anuradhapura DL1b Lowland vs. Matale IL1a Upland | Agro-ecological zones of Sri Lanka (DOA) | Confirm Profile A as the primary engine demo benchmark. |
| **Crop Water Requirements** | Rice 1050mm, Maize 550mm, Mung 350mm, Chilli 600mm | FAO 33, FAO 56, DOA RRDI/FCRDI guides | Verify whether nominal gross values align with water-budget calculation. |
| **Crop Durations** | BG rice 105d, Mung 60-65d, Maize 110d, Chilli 140d | DOA FCRDI variety registry | Approve maturity ranges. |
| **Legume Bonus** | $+15\%$ to $+25\%$ ($\alpha_{\text{legume}} = 0.20$) | Peoples et al. (1995), Herridge et al. (2008), DOA (2021) | Calibrate bonus weight in scoring engine. |
| **Diversity Threshold** | $D \ge 0.6$ ($N_{\text{unique}} \ge 3$) | FAO CA Guidelines | Decide between ratio $D \ge 0.6$ or integer count $N \ge 3$. |
| **Yala Cutoff** | $700\text{ mm}$ total available water | FAO 33 ($K_y > 1.0$), Bethma protocol | Validate threshold with Matheesha's irrigation input. |

## Financial formula review

Bhagya approved the deterministic range formulas in Shehani's commit `03a46b7`
subject to provenance and wording changes. Formula approval does not approve
the synthetic worked-example prices, costs, or yields. See
[`FINANCIAL_SPECIFICATION.md`](FINANCIAL_SPECIFICATION.md) for the versioned
calculation, missing-data behavior, required sources, and implementation
conditions.
