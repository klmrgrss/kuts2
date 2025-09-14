# Estonian Construction Qualifications — Domain Knowledge (EEEL)

> Purpose: compact, citable domain knowledge for LLM features and code generation.  
> Authority: Estonian originals control; English summaries are convenience only. Where rules matter, quote the Estonian text and cite the source PDF.  

---

## 1) Purpose & scope
This document grounds LLMs and developers who build features around the Estonian construction-sector qualifications administered by EEEL (Eesti Ehitusettevõtjate Liit). It summarizes **how qualifications work**, what **levels and specialisations** exist, and the **application/recertification** rules. It also includes **JSON/YAML schemas** so your codebase can derive machine-readable data.  
The authoritative source of truth is the **Estonian-language standards and procedures (kutsestandard; kutse andmise kord – “KA kord”)** approved by the relevant **Kutsenõukogu**. English in this file is only an explanatory layer. [EJ6-Kord] [TJ5-Kord]

---

## 2) Mental model of the system (who / what / flow)
- **Kutsestandard** defines competence requirements per qualification; after positive assessment, a **kutsetunnistus** is issued. [EJ6-Kord] [TJ5-Kord]  
- **KA kord** sets **eligibility, documents, and assessment methods** for initial applications and **taastõendamine** (recertification). Fees are charged per Kutseseadus §17 and approved by Kutsenõukogu. [EJ6-Kord] [TJ5-Kord]  
- Key tracks used here: **Level 4 oskustöölised**, **Level 5 Ehituse tööjuht (TJ5)**, and **Level 6 Ehitusjuht (EJ6)**. Standards are versioned; for example, **EJ6 v12** was confirmed on **08.02.2024** and **valid to 07.02.2026**. [EJ6-Std]

---

## 3) Glossary (EN ↔ ET) with stable IDs
> Use these IDs across your codebase and prompts. Keep Estonian as the authoritative label.

| id | en_label | et_label | short_definition_en | source |
|---|---|---|---|---|
| `kutsestandard` | occupational standard | kutsestandard | Defines tasks/competence for a qualification; basis for training & issuing certificates. | [Kutseseadus] |
| `ka_kord` | issuing procedure | kutse andmise kord | Procedure covering eligibility, documents, assessment, and fees for issuing/renewing a qualification. | [EJ6-Kord] [TJ5-Kord] |
| `esmane_kutse` | initial award | esmane kutse | First-time application per KA kord eligibility. | [TJ5-Kord] |
| `taastõendamine` | recertification | taastõendamine | Renewal of a prior, not-long-expired qualification per KA kord. | [EJ6-Kord] |
| `ehitusjuht_tase_6` | construction site manager L6 | Ehitusjuht, tase 6 | Level 6 manager; 5 specialisations. | [EJ6-Std] |
| `toojuht_tase_5` | construction foreman L5 | Ehituse tööjuht, tase 5 | Level 5 foreman; specialisations including general building, HVAC, VK, finishing, special works. | [TJ5-Std] |
| `oskustööline_l4` | skilled worker L4 | oskustöölise kutse | Trades procedures for general/special works. | [Osku-Kord] [Eri-Kord] |
| `mtr_pädev_isik` | competent person in registry | pädev isik MTR-is | Person who can be entered in MTR as competent for regulated work. | [MTR] |
| `cc1` | consequence class CC1 | CC1 | Simplest consequence class per EVS‑EN 1990; limits where TJ5 may act independently. | [TJ5-Guide] |
| `kasutusotstarbe_koodid` | use codes | kasutamise otstarbe koodid | 11100 (1‑dwelling), 11210 (2‑dwelling), 11221 (row house) — TJ5 independent limits. | [TJ5-Guide] |

---

## 4) Qualification levels (supported in this app)

### 4.1 Level 4 — Oskustöölised (selected trades)
**Tracks covered by two KA-kord documents** (general/finishing/environmental tech; and special works like roofs/sheet metal). Initial application generally requires **at least basic education** and passing a **theoretical (and/or combined) exam**, with specified **documents**; recertification requires a **still-recent qualification**, **experience or teacher experience**, and a **written test** plus documents. See the exact lists below. [Osku-Kord] [Eri-Kord]

**Initial (esmakordne) — documents (examples from general/finishing/env. tech):**  
- Application form (EEEL), ID copy, education proof, **work activity description**, **MTA employment registry proof (3y)**, employer letter on demand; **theoretical exam** required. [Osku-Kord]  
**Recertification (taastõendamine) — prerequisites & documents:**  
- Prior qualification not expired >1y; either **2y relevant experience in last 5y** or **3y as VET teacher in last 5y**; **written test**; submit application, ID copy, prior certificate copy (if on paper), work activity description, MTA registry proof, employer letter if asked. [EJ6-Std]

> **Note:** For “eriehitustööd oskustöölised” (e.g., **lame-/kaldkatused, plekksepp**), the KA kord mirrors the same structure: basic education, **combined exam (theory+practical)** for initial, and similar recert conditions. [Eri-Kord]

---

### 4.2 Level 5 — **Ehituse tööjuht (tase 5, “TJ5”)**
**Specialisations & structure** (from the standard): general building, HVAC (sisekliima), **VK** (hoonesisene vee- ja kanalisatsioon), finishing, special works. For some tracks you can prove **full specialisation** or a **narrow competence** (valikkompetents). [TJ5-Std]

**Regulated vs voluntary & where TJ5 can act independently:**  
- **Regulated** (can be a **pädev isik** in MTR and act independently): **general building, HVAC, VK** — but limited to **use codes 11100/11210/11221** and **CC1** buildings; complex works only under ≥L6 specialist. [TJ5-Guide]  
- **Voluntary** (qualification not legally required; **cannot** be MTR pädev isik): **finishing** and **special works** (e.g., painting, tiling, roofing, sheet metal). [TJ5-Guide]

**Application prerequisites are defined as “packages” (Variant I–V) in the KA kord.** A few examples:  
- **Variant I:** prior matching **Level 4 (fixed-term)** + **upper‑secondary education** + **≥3y** management experience (≥2y matching) + **base training ≥30 hours**. [TJ5-Kord]  
- **Variant II:** **upper‑secondary education** + **≥5y** management experience in last 10y (≥2y recent) + **base training ≥30h**; may require **technology exams** if no matching prior qualification. [TJ5-Kord]  
- **Variant IV/V:** higher/technical education-based routes with experience and base trainings (see full text). [TJ5-Kord]

> **Selection & declaration on the application:** You must specify **the specialisation** and, if applicable, a **narrow competence** on the application form. [TJ5-Kord]

---

### 4.3 Level 6 — **Ehitusjuht (tase 6, “EJ6”)**
**Five specialisations** in the standard: **general building; indoor climate systems; VK (indoor water & sewer); ÜVK (public water & sewer); owner’s supervision**. For **general building** and **indoor climate**, candidates can prove either **full specialisation** or a **narrow field** (e.g., **kivi/betoon/puit/teras/lammutus/fassaad**; **küte/jahutus/vent**). [EJ6-Std]

**Scope & limits (examples from the standard for general building):**  
- Up to **45 m height** and **8 m depth**, with span limits: **monolithic concrete 18 m**, **precast concrete 25 m**, **steel 36 m**, **timber 18 m**, **composite 18 m**; up to **geotechnical category 2** structures; certain **internal roads/areas** in simple conditions. [EJ6-Std]  
- ÜVK scope examples: **water pipelines ≤300 mm**, **sewer ≤1000 mm**, **WWTP 5000 IE not on poorly protected aquifers**, **water treatment ≤2500 m³/d**. [EJ6-Std]

**Initial application (EJ6) — documents & combos (KA kord):**  
- **Eligibility packages** by degree length (300/240/180 EAP) combined with **matching experience windows** and, when applicable, **base training (≥40h)**; submit: application, work-activity description, ID, **education + transcript**, **ENIC/NARIC** (if foreign), **training proofs**, **MTA 3‑y employment registry proof**, and **B2 Estonian** proof on request. [EJ6-Kord] [Osku-Kord]

**Recertification (EJ6):**  
- Prior EJ6 not expired >1y; **≥2y** matching work in last 5y, and **continuing education** comprising **(1) construction management 16 ak/h** and **(2) specialisation-specific 16 ak/h per activity**, or **owner’s supervision 16 ak/h** as applicable, within last 5 years. [EJ6-Kord] [EJ6-Recert-Guide]

---

### 4.4 Activities & valikkompetents mapping (L5 & L6)
Use this canonical table to keep LLM and UI aligned on what **narrow fields** are included in each **full specialisation** (excerpted):  
- **EJ6:** Üldehituslik ehitamine ⟶ *kivi- ja betoon*, *puit*, *teras*, *lammutus*, *fassaad*; Sisekliima ⟶ *küte*, *jahutus*, *vent*; VK; ÜVK; Omanikujärelevalve. [Activity-Map]  
- **TJ5:** Üldehitustööd ⟶ *kivi*, *betoon*, *puit*, *monteeritavad konstruktsioonid*; Sisekliima ⟶ *küte*, *jahutus*, *vent*; VK; **Finishing** ⟶ *maalri*, *plaatija*, *põrandakate*, *krohvimine*; **Eriehitustööd** ⟶ *lamekatus*, *kaldkatus*, *plekksepp*. [TJ5-Std]

---

## 5) Application process (common skeleton)

1) **Choose qualification & specialisation(s)** (up to three for EJ6 in one application). [EJ6-Kord]  
2) **Check eligibility package** (KA kord variants). Use the **packages** below to programmatically evaluate candidates. [TJ5-Kord] [EJ6-Kord]  
3) **Prepare documents** (IDs below).  
4) **Pay the fee** (per Kutseseadus §17; set by kutseandja; approved by Kutsenõukogu). [EJ6-Kord] [TJ5-Kord]  
5) **Assessment** per qualification (document review; theory/practical; interview/test as required). [EJ6-Kord] [EJ6-Std]  
6) **Decision & register**: if positive, issue certificate and publish in **Kutseregister** per rules. [EJ6-Kord]

### 5.1 Documents (stable IDs for code)
- `application_form_eeel`, `id_copy`, `education_proof`, `transcript_or_diploma_supplement`, `work_activity_description`, `training_proofs_pdf`, `mta_registry_proof_3y`, `previous_certificate_copy` (recert), `enic_naric_equivalence` (if foreign), `language_b2_proof_optional_on_request`. [Osku-Kord] [EJ6-Kord]

### 5.2 Exam types (level-dependent)
- **L4**: theoretical (and some tracks combined theory+practical). [Osku-Kord] [Eri-Kord]  
- **TJ5**: assessment from documents; in some paths **technology exams** for full specialisation. [TJ5-Guide]  
- **EJ6**: document-based assessment; **oral interview and/or written test** as needed during pre‑evaluation. [EJ6-Kord]

---

## 6) Normative Estonian snippets (ready to quote)
> Keep these concise blocks for LLM quoting; always retain the citation.

**TJ5 — regulated vs voluntary & independence limits (excerpt):**  
„… võib tegutseda iseseisvalt ja omal vastutusel … järgmistel tegevusaladel: **üldehitustööd; sisekliima; VK** … ainult järgnevalt kirjeldatud piirangute ulatuses: **11100, 11210, 11221** ning **CC1**. Keerukamate objektide ehitamisel … ainult alltöövõtu korras **≥EKR 6** vastutusel.“ [TJ5-Guide]

**EJ6 — five specialisations & scope thresholds (excerpt):**  
„Ehitusjuhi kutse koosneb viiest spetsialiseerumisest… [loetelu]. … iseseisvalt … **kuni 45 m** kõrgused ja **8 m** sügavused; sillete piirangud: **18 m monoliit**, **25 m monteeritav**, **36 m teras**, **18 m puit/komposiit** … **kuni 2. geotehniline kategooria**…“ [EJ6-Std]

**L4 — initial & recert highlights (excerpt):**  
„Esmakordne: **vähemalt põhiharidus**; **teoreetiline (kirjalik ja/või suuline)** või kombineeritud eksam; esitatavad dokumendid: **avaldus, ID, haridus** (+ tööalase tegevuse kirjeldus, MTA tõend). Taastõendamine: varasem kutse mitte aegunud >1 a; **2 a** kogemus viimase **5 a** jooksul või **3 a** kutseõpetajana; **kirjalik erialane test** + dokumendid.“ [Osku-Kord]

---

## 7) JSON/YAML schemas (for codegen)

### 7.1 Qualification schema (example: EJ6)
```yaml
qualification:
  id: "ehitusjuht_tase_6"
  estqf_level: 6
  name_en: "Construction Site Manager"
  name_et: "Ehitusjuht"
  standard_version: "12"            # per standard
  valid_until: "2026-02-07"         # per standard
  specialisations:
    - id: "yldehitus"
      name_et: "Üldehituslik ehitamine"
      narrow_fields: ["kivi_betoon", "puit", "teras", "lammutus", "fassaad"]
    - id: "sisekliima"
      name_et: "Sisekliima tagamise süsteemide ehitamine"
      narrow_fields: ["kyte", "jahutus", "ventilatsioon"]
    - { id: "vk_hoonesisene", name_et: "Hoonesisese või selle juurde kuuluva veevarustuse ja kanalisatsioonisüsteemi ehitamine" }
    - { id: "uvk", name_et: "Ühisveevärgi või kanalisatsiooni ehitamine" }
    - { id: "omanikujarelevalve", name_et: "Omanikujärelevalve tegemine" }
  scope_limits_ref: "ehitusjuht_tase_6.standard.scope"
  sources:
    - type: "standard"
      cite: "ehitusjuht_tase_6.6.pdf"   # keep filename in your repo
```
(Version & validity per standard meta; specialisations & narrow fields per A‑osa.) [EJ6-Std]

### 7.2 Eligibility “packages” schema (example: TJ5)
```json
{
  "qualification_id": "toojuht_tase_5",
  "packages": [
    {
      "id": "variant_1",
      "education": "upper_secondary",
      "prior_cert": "level_4_matching_fixed_term",
      "experience": { "years_total": 3, "years_matching": 2, "window_years": 5, "role_examples": ["brigadir","meister","tööjuht"] },
      "trainings": [{ "kind": "base_mgmt", "hours_min": 30 }]
    },
    {
      "id": "variant_2",
      "education": "upper_secondary",
      "experience": { "years_total": 5, "years_recent": 2, "window_years": 10 },
      "trainings": [{ "kind": "base_mgmt", "hours_min": 30 }],
      "notes": "If no matching prior qualification, technology exams may apply for full specialisation."
    },
    { "id": "variant_4_or_5", "education": "higher_or_technical", "experience": "see KA kord 2.1.4–2.1.5", "trainings": [{"kind":"base_mgmt","hours_min":30}] }
  ]
}
```
(Packages mirror KA kord §2.1.1–2.1.5 and the “Selgitused” matrices.) [TJ5-Kord]

### 7.3 Document checklist schema (example, EJ6 initial)
```yaml
documents_required:
  - application_form_eeel
  - work_activity_description
  - id_copy
  - education_proof
  - transcript_or_diploma_supplement
  - enic_naric_equivalence      # if foreign education
  - training_proofs_pdf         # if trainings required by your route
  - mta_registry_proof_3y
  - language_b2_proof_optional_on_request
```
(See KA kord 2.7 items a–g.) [EJ6-Kord]

### 7.4 “Scope & limits” schema (example, EJ6 general building)
```json
{
  "qualification_id": "ehitusjuht_tase_6",
  "scope": {
    "general_building": {
      "height_max_m": 45,
      "depth_max_m": 8,
      "spans_m": { "monolithic_concrete": 18, "precast_concrete": 25, "steel": 36, "timber": 18, "composite": 18 },
      "geotechnical_category_max": 2
    },
    "uvk": { "water_diameter_max_mm": 300, "sewer_diameter_max_mm": 1000, "wastewater_load_max_ie": 5000, "water_treatment_capacity_max_m3_per_d": 2500 }
  }
}
```
(From EJ6 standard scope text.) [EJ6-Std]

### 7.5 TJ5 independence limits (for programmatic checks)
```yaml
toojuht_tase_5_limits:
  can_be_mtr_competent_on:
    - general_building
    - indoor_climate_systems
    - vk_hoonesisene
  only_if:
    usage_codes: [11100, 11210, 11221]
    consequence_class: CC1
  else_requires_supervision_by_level6: true
```
(Per standard/selgitused.) [TJ5-Guide]

---

## 8) Decision rules & worked examples

**Example A — “Is this candidate eligible for TJ5 under Variant II?”**  
Inputs: upper‑secondary; 5y total experience in last 10y (2y in last 5y), base training ≥30h.  
Decision: **Eligible under Variant II** (documents must evidence the specific specialisation). [TJ5-Kord]

**Example B — “Can a TJ5 act as MTR pädev isik for 11221 row house HVAC?”**  
Yes — TJ5 may act independently on **regulated specialisations** within **11100/11210/11221** & **CC1** limits. Otherwise, require ≥L6 oversight. [TJ5-Guide]

**Example C — “EJ6 recert training hours calculation.”**  
For one specialisation (e.g., Üldehituslik), provide **16 ak/h construction-management** + **16 ak/h specialisation-specific** within the last 5y. **If multiple specialisations are renewed**, the **management 16 ak/h** is still one bucket, but **each specialisation** requires its **own 16 ak/h** relevant training. [EJ6-Kord] [EJ6-Recert-Guide]

---

## 9) LLM guardrails (important)
- **When uncertain, quote the Estonian paragraph and include the citation marker from this file.**  
- **Never overstate MTR eligibility**: for **TJ5**, enforce **11100/11210/11221** and **CC1**; for more complex cases require **≥L6** supervision. [TJ5-Guide]  
- **Respect package logic** exactly; if a field is missing, respond with “insufficient evidence per KA kord §…”. [TJ5-Kord] [EJ6-Kord]

---

## 10) Change log & versions (pin these to your repo)
- **EJ6 KA kord**: *Viimati muudetud* **13.04.2023** otsus nr 47. [EJ6-Kord]  
- **TJ5 KA kord**: *Viimati muudetud* **20.02.2023** otsus nr 46. [TJ5-Kord]  
- **EJ6 standard**: **Otsus 08.02.2024**, **kehtib kuni 07.02.2026**, **versioon 12**. [EJ6-Std]  
- **TJ5 standard**: **Otsus 22.01.2021**, **kehtib kuni 21.01.2026**, **versioon 4**. [TJ5-Std]

---

## 11) Sources

*   `[EJ6-Kord]`: `Ehitusjuht-tase-6-KA-kord-13.04.2023-8.pdf` (KA kord EJ6)
*   `[TJ5-Kord]`: `Ehituse-toojuht-tase-5-KA-kord-20.02.2023-1.pdf` (KA kord TJ5)
*   `[EJ6-Std]`: `ehitusjuht_tase_6.6.pdf` (EJ6 standard v12)
*   `[TJ5-Std]`: `11_TJ5_standard_kinnitatud_2201_2021.pdf` (TJ5 standard v4)
*   `[Osku-Kord]`: `Uldehituse-ehitusviimistluse-ja-keskkonnatehnika-oskustooliste-kutsete-KA-kord-20.02.2023.pdf` (oskustöölised – general/finishing/env.tech)
*   `[Eri-Kord]`: `Kord_02_Eriehitustoode_oskustooliste_kutsete_KAK_1904_2022.pdf` (oskustöölised – eriehitused)
*   `[EJ6-Recert-Guide]`: `Selgitus_EJ6_taastoendaja_koolituste_kohta_mai_2022.pdf` (EJ6 recert training guide)
*   `[TJ5-Guide]`: `05_Selgitused_2021_korra_alusel_TJ5_taotlejatele-1.pdf` (TJ5 applicant explanations)
*   `[Activity-Map]`: `04_Tegevusalade_loetelu_tasemed_5_ja_6.pdf` (activity ↔ valikkompetents mapping)

---

### Appendix A — Minimal bilingual glossary entries (expand as needed)
```yaml
terms:
  - id: kutsestandard
    en_label: occupational_standard
    et_label: kutsestandard
    definition_en: Defines the competence for a qualification; basis for training and issuing certificates.
    source: ehitusjuht_tase_6.6.pdf
  - id: ka_kord
    en_label: issuing_procedure
    et_label: kutse_andmise_kord
    definition_en: Procedure describing eligibility, documents, assessment, fees, and decision mechanics.
    source: Ehitusjuht-tase-6-KA-kord-13.04.2023-8.pdf
  - id: esmase_taotlemine
    en_label: initial_application
    et_label: esmakordne_taotlemine
    definition_en: First-time application route per KA kord eligibility packages.
    source: Ehituse-toojuht-tase-5-KA-kord-20.02.2023-1.pdf
  - id: taastõendamine
    en_label: recertification
    et_label: taastõendamine
    definition_en: Renewal of an earlier certificate within the lapse window, meeting experience and CPD rules.
    source: Ehitusjuht-tase-6-KA-kord-13.04.2023-8.pdf
```