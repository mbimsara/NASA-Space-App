# Agronomy and financial model register

Owner/reviewer: Bhagya. Research: Tharuka. Financial implementation and catalog validation: Shehani.

> [!IMPORTANT]
> **Status: DRAFT / RESEARCH PENDING.** No scientific rule or crop value is marked as approved. Values and constraints documented below represent referenced research drafts by Tharuka for Bhagya's formal review. Uncertain or unverified values are preserved as unmeasured/unapproved rather than converted to zero or default assumptions.

---

## Demonstration region confirmation

* **Demonstration focus:** Sri Lanka Dry and Intermediate Zones (Demonstration centroid: Anuradhapura Low-Country Dry Zone `[8.3°N, 80.4°E]` / Matale Intermediate Zone `[7.5°N, 80.6°E]`).
* **Justification:** Reflects the dual-season cropping dynamics (*Maha* major northeast monsoon season, Oct–Feb; *Yala* minor southwest dry season, Mar–Aug). The primary agronomic challenge in this region is the transition from lowland flooded paddy during Maha to water-efficient Other Field Crops (OFCs) and grain legumes during Yala under restricted tank storage.
* **Demonstration catalog draft:** 8 crops compiled in [`data/catalogs/crops.json`](../data/catalogs/crops.json) (Rice, Mung bean, Maize, Groundnut, Cowpea, Finger millet, Black gram, Chilli) aligned with the Figma MVP prototype.

---

## Rule Register Specifications

### RULE-ROT-001-v0.1: Consecutive Same-Crop Repetition Constraint

| Field | Detail |
| --- | --- |
| **Rule ID and version** | `RULE-ROT-001-v0.1` |
| **Input and units** | Candidate sequence of crop IDs `[crop_t-1, crop_t]`; boolean policy flag `forbid_consecutive_crop`. If previous crop is unknown (`None`), rule evaluates only adjacent pairs within the generated sequence. |
| **Applicability** | All regions (Dry, Intermediate, Wet zones); applies across all seasons (Maha to Yala, Yala to Maha). |
| **Calculation / constraint** | Hard exclusion when enabled: Reject candidate if `crop_t == crop_t-1`. (Optional softening to rank penalty pending Bhagya's review). |
| **Evidence** | **Department of Agriculture (DOA) Sri Lanka Guidelines & FAO Pest Management:** Continuous monoculture of identical crops amplifies specialized host-specific soil-borne pathogens, root-knot nematodes (*Meloidogyne spp.*), and weed seedbanks. In Sri Lankan paddy systems, continuous non-flooded monocropping severely increases weed competition. Access date: 2026-11-14. URL: `https://doa.gov.lk/rrdi/` |
| **Assumptions vs Limitations** | *Evidence:* Repeating identical crops accelerates pathogen cycles. *Assumption:* Hard exclusion is agronomically conservative; however, smallholder farmers with dedicated lowland paddy fields frequently cultivate rice-rice where major irrigation is guaranteed. Rule must allow policy toggling. |
| **Review** | Researcher: Tharuka. Status: **Draft — Pending Bhagya review**. Unresolved question: Should rice-rice be exempted in Major Irrigation Schemes (e.g., Mahaweli System H) when tank capacity exceeds 80%? |
| **Example** | Input: `("rice", "rice", "mung-bean")`. Outcome: Candidate rejected under `forbid_consecutive_crop = True`. Edge case: Previous season crop unknown (`None`) $\rightarrow$ evaluate only internal sequence pairs. |

---

### RULE-ROT-002-v0.1: Consecutive Botanical Family Repetition Constraint

| Field | Detail |
| --- | --- |
| **Rule ID and version** | `RULE-ROT-002-v0.1` |
| **Input and units** | Candidate sequence of botanical families `[family_t-1, family_t]`; boolean policy flag `forbid_consecutive_family`. If crop family is unknown/null, flag candidate for validation error. |
| **Applicability** | Dry and Intermediate Zones; particularly critical for *Solanaceae* (Chilli, Tomato, Brinjal) and *Fabaceae* / *Poaceae*. |
| **Calculation / constraint** | Hard exclusion when enabled: Reject candidate if `family_t == family_t-1`. |
| **Evidence** | **Field Crops Research and Development Institute (FCRDI Mahailluppallama):** Pests and diseases share cross-crop hosts within botanical families (e.g., anthracnose, bacterial wilt *Ralstonia solanacearum*, and geminiviruses across *Solanaceae*; shoot fly and stem borers across *Poaceae* such as maize and sorghum). Rotating families breaks pest reproduction cycles. Access date: 2026-11-14. URL: `https://doa.gov.lk/fcrdi-mahailluppallama/` |
| **Assumptions vs Limitations** | *Assumption:* Consecutive *Poaceae* (e.g., Rice $\rightarrow$ Maize) is common in practice but suboptimal for soil nutrient balancing due to high nitrogen extraction. *Limitation:* Strictly forbidding consecutive *Poaceae* would eliminate Rice $\rightarrow$ Maize rotations unless specific inter-family exceptions are defined. |
| **Review** | Researcher: Tharuka. Status: **Draft — Pending Bhagya review**. Unresolved question: Should the engine support a granular "family-specific" rule (strict for Solanaceae, conditional for Poaceae) rather than a global boolean? |
| **Example** | Input: `("chilli", "chilli", "maize")` with families `("Solanaceae", "Solanaceae", "Poaceae")`. Outcome: Rejected when `forbid_consecutive_family = True`. |

---

### RULE-SOIL-001-v0.1: Legume Biological Nitrogen Fixation & Soil Diversity Benefit

| Field | Detail |
| --- | --- |
| **Rule ID and version** | `RULE-SOIL-001-v0.1` |
| **Input and units** | Crop botanical family (`Fabaceae`); previous crop family; seasonal duration (days). |
| **Applicability** | All Sri Lankan agro-ecological regions; upland RBE and well-drained lowland rice fallows. |
| **Calculation / constraint** | Ranking score bonus (Soft preference, weight $\alpha_{\text{soil}} \in [0.0, 1.0]$): Add $+15\%$ to $+25\%$ soil health score component when a *Fabaceae* crop (Mung bean, Cowpea, Groundnut, Black gram) follows a *Poaceae* grain (Rice, Maize). |
| **Evidence** | **DOA Sri Lanka & HARTI Agronomy Bulletins:** Grain legumes fix atmospheric nitrogen ($30–60\text{ kg N/ha}$ through symbiotic *Rhizobium* nodules), leaving residual nitrogen ($15–30\text{ kg N/ha}$) that reduces synthetic nitrogen fertilizer requirement for subsequent cereal crops while improving soil organic matter and soil microbial activity. Access date: 2026-11-14. URL: `https://doa.gov.lk/fcrdi-mahailluppallama/` |
| **Assumptions vs Limitations** | *Evidence:* Legumes contribute positive net nitrogen and break monoculture depletion. *Assumption:* Do NOT claim measured field nitrogen increases without a laboratory soil test. The score bonus serves solely as a relative agronomic heuristic. |
| **Review** | Researcher: Tharuka. Status: **Draft — Pending Bhagya review**. Unresolved question: Should short-duration pulses (mung bean, 65d) receive identical benefit scores to longer-duration groundnuts (105d)? |
| **Example** | Input Plan A: `Rice -> Mung bean -> Rice`. Input Plan B: `Rice -> Maize -> Rice`. Outcome: Plan A receives a positive soil diversity boost over Plan B. |

---

### RULE-SOIL-002-v0.1: Multi-Season Crop Diversity Index

| Field | Detail |
| --- | --- |
| **Rule ID and version** | `RULE-SOIL-002-v0.1` |
| **Input and units** | Distinct crop count $N_{\text{unique}}$ over rotation length $L \in [3, 5]$. |
| **Applicability** | Multi-season rotation evaluation across all zones. |
| **Calculation / constraint** | Diversity ratio $D = N_{\text{unique}} / L$. Rotations with $D \ge 0.6$ receive ranking preference over sequences with repeated crops. |
| **Evidence** | **FAO Conservation Agriculture Guidelines:** Multi-crop rotations maintain root diversity at differing soil depths, reducing compaction and improving structural soil health compared to 2-crop oscillations. Access date: 2026-11-14. |
| **Assumptions vs Limitations** | *Assumption:* Higher rotational diversity improves long-term ecological resilience. *Limitation:* Does not account for seed market availability or farmer operational specialization. |
| **Review** | Researcher: Tharuka. Status: **Draft — Pending Bhagya review**. |
| **Example** | Input Plan 1 (4 seasons): `Rice -> Mung bean -> Maize -> Groundnut` ($D = 4/4 = 1.0$). Input Plan 2: `Rice -> Mung bean -> Rice -> Mung bean` ($D = 2/4 = 0.5$). Outcome: Plan 1 scores higher in the rotational diversity sub-metric. |

---

### RULE-EXCL-001-v0.1: Yala Season Lowland Water Deficit Exclusion

| Field | Detail |
| --- | --- |
| **Rule ID and version** | `RULE-EXCL-001-v0.1` |
| **Input and units** | Season identifier (`yala`); irrigation availability flag / storage level (`irrigation_supply_mm_per_season` or tank status). |
| **Applicability** | Dry Zone (e.g., Anuradhapura, Polonnaruwa) minor irrigation schemes and rainfed lowlands. |
| **Calculation / constraint** | Hard exclusion or critical warning: If `season == "yala"` AND `irrigation_supply_mm_per_season < 700` (or minor tank storage $< 50\%$), exclude `rice` (water demand $\approx 1050\text{ mm}$) and restrict candidates to low-water OFCs (demand $\le 450\text{ mm}$). |
| **Evidence** | **Sri Lanka Department of Irrigation & Department of Agriculture (Bethma system):** Under water deficits in Yala, water rationing is enforced. Farmers cultivate non-rice OFCs (green gram, cowpea) to achieve full harvest on limited storage. Access date: 2026-11-14. URL: `https://doa.gov.lk/rrdi/` |
| **Assumptions vs Limitations** | *Evidence:* Yala rainfall in the Dry Zone averages $< 350\text{ mm}$, insufficient for flood-irrigated paddy. *Assumption:* Threshold of $700\text{ mm}$ total water is indicative and subject to tank replenishment model verification by Matheesha and Bhagya. |
| **Review** | Researcher: Tharuka. Status: **Draft — Pending Bhagya review**. Unresolved question: How should the engine behave if irrigation supply is unknown (`None`)? Currently defaults to non-exclusion with an explicit "unverified water risk" note. |
| **Example** | Input: `season="yala"`, `irrigation_supply_mm_per_season=300`. Outcome: `rice` excluded; `mung-bean`, `cowpea`, `finger-millet` remain eligible. |

---

### RULE-EXCL-002-v0.1: Poorly Drained Lowland Soil Incompatibility

| Field | Detail |
| --- | --- |
| **Rule ID and version** | `RULE-EXCL-002-v0.1` |
| **Input and units** | Soil drainage class / landform (`lowland_poorly_drained` vs `upland_well_drained`). Unknown input handled by skipping exclusion and flagging data gap. |
| **Applicability** | Ill-drained Low Humic Gley (LHG) soils in valley bottoms across Dry and Intermediate Zones. |
| **Calculation / constraint** | Hard exclusion: When soil condition is specified as `lowland_poorly_drained`, exclude upland crops highly susceptible to root asphyxiation and damping-off (`maize`, `chilli`, `groundnut`) during periods with heavy standing water. |
| **Evidence** | **Department of Agriculture Soils & Plant Nutrition Division:** Maize and Chilli cannot tolerate standing water or poor internal drainage for $> 24-48\text{ hours}$, leading to collar rot (*Phytophthora*) and severe root death. Access date: 2026-11-14. URL: `https://doa.gov.lk/fcrdi-mahailluppallama/` |
| **Assumptions vs Limitations** | *Evidence:* Soil drainage is a primary physical barrier to crop success. *Assumption:* In synthetic demo fixtures, soil drainage is often unspecified (`None`); the engine must NOT assume well-drained conditions without verification. |
| **Review** | Researcher: Tharuka. Status: **Draft — Pending Bhagya review**. Unresolved question: Can ridge-and-furrow bed preparation mitigate drainage constraints for Maize in intermediate seasons? |
| **Example** | Input: Landform = `lowland_poorly_drained`, Season = `maha`. Outcome: `maize` and `chilli` excluded; `rice` remains eligible. |

---

## Status and Next Steps

1. Tharuka has completed the initial referenced draft catalog ([`crops.json`](../data/catalogs/crops.json)) and agronomy rules register ([`AGRONOMY_RULES.md`](AGRONOMY_RULES.md)).
2. Scientific review by Bhagya:
   - Validate water demand figures (mm/cycle).
   - Confirm policy flags (hard exclusion vs penalty scoring).
   - Formally approve catalog items (`review_status: "approved"`).
3. Shehani implements scoring and priority weights based on approved rules once Bhagya signs off.

## Financial formula review

Bhagya approved the deterministic range formulas in Shehani's commit `03a46b7`
subject to provenance and wording changes. Formula approval does not approve
the synthetic worked-example prices, costs, or yields. See
[`FINANCIAL_SPECIFICATION.md`](FINANCIAL_SPECIFICATION.md) for the versioned
calculation, missing-data behavior, required sources, and implementation
conditions.
