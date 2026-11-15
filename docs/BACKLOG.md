# First milestone backlog

Create issues from this list; these are planning entries, not issues already created in GitHub. Target milestone: one connected farm-to-plan journey. Agree on contracts and fixtures first.

| Task | Owner | Depends on | Acceptance |
| --- | --- | --- | --- |
| Confirm schemas and error conventions | Dulanjaya + all reviewers | None | Owners approve fields/units/version handling |
| Core Figma flow/components | Tharuka | Core journey | Shehani can implement farm and comparison screens |
| Crop catalog research and approval | Tharuka + Bhagya | Region/season scope | Sourced usable entries approved by Bhagya |
| NASA feasibility and first adapter | Matheesha | Demo location/date range | Real normalized response with provenance |
| Backend scaffold and farm persistence | Dulanjaya | Schemas | Farm save/read/update, validation, documented startup |
| Frontend scaffold and farm form | Shehani | Design/contracts | Responsive form, validation, typed API client |
| Rotation and water functions | Bhagya | Approved catalog + climate contract | Constraints/reasons and reviewed numeric examples |
| Catalog loading validator | Shehani | Catalog schema | Invalid entries rejected; approved entries accepted |
| Assistant over approved fixture results | Akash | Analysis contract | Numbers/context correct; missing data acknowledged |
| Integrate core flow | Dulanjaya + everyone | Above | Save farm → observations → rotations → explanation |
| Scenario and selected-plan persistence | Bhagya + Matheesha + Dulanjaya + Shehani | Connected flow | Baseline preserved; recalculation and reopening work |
| Usability and grounded-answer review | Tharuka + Akash + Shehani | Connected flow | Findings recorded and blocking defects resolved |

Implemented since this backlog was drafted: finance calculator v0.1, immutable saved-plan reports, action-calendar/ICS export, season feedback, registered-farm climate twins, and an optional grounded LLM wording layer. Remaining research-dependent work is SoilRevive/FarmRecovery rule review, validated weed-image analysis, offline writes/conflict policy, reminder delivery, and reviewed multilingual assistant/voice behavior. See the implementation plan for ownership; do not treat those remaining items as implemented.
