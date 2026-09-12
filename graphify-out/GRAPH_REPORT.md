# Graph Report - Hydride_Machine_learning_project  (2026-09-12)

## Corpus Check
- 258 files · ~496,637 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5063 nodes · 12005 edges · 172 communities (157 shown, 15 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 839 edges (avg confidence: 0.58)
- Token cost: 98,314 input · 0 output

## Community Hubs (Navigation)
- Featuriser Element Tables
- Prediction Request Path
- Delivery Refusal Vocabulary
- Leak Sentinels
- Canonical Composition Key
- Descriptor Feature Contract
- Keyed Feature Merge
- External Libraries and Archival Report
- Element Mover's Distance Novelty
- Surrogate Prediction Interface
- Feature Selection Inside Folds
- Smoke Pipeline Fixture
- Screen Protocol Runner
- Delivery Contract Types
- Quantile Model Fitting
- Leak Inventory
- Raw Data Loaders
- Descriptor Computability
- Gate Harness Registry
- Conformal Calibration
- Artifact Manifest
- Surrogate Training Run
- Calibrated Quantile Heads
- Applicability Domain Screen
- Artifact Store Promotion
- Grouped Data Splits
- Gate CLI Reporting
- Acceptance Criteria Gates
- Comparison
- Comparison
- Contract
- Ac3 Conformal Coverage
- Config
- Load
- Benchmark
- Loco
- Element Data
- Stats
- Ac2 Parity
- Validation
- 059 Pymoo Problem Definition
- Model
- Evaluate
- L3 L10 Holdout Immutability
- Composites
- Validation
- Window
- Promote
- Clean
- Ac3 Coverage
- Hg2 Refusal Path
- Selection
- Validation
- Metadata
- Deploy
- Protocol
- Novelty
- Store
- L7 L8 Grouping
- Domain
- Metamorphic
- Store
- Target
- Ac6 Loco
- L2 L4 Model Selection
- Ac4 Round Trip
- L1 L5 Early Stopping
- L12 Sample Weights
- Screening
- L9 Keyed Merge
- Evaluate
- Loco
- Conftest
- L11 Explainability
- L13 Class Survival
- Scaler
- Scaler
- 016 Element Property Tables
- Golden
- Check Board
- No Leak
- Init
- Ac1 Reproducibility
- L6 Selection Independence
- 014 Cleanlab Screening As
- 048 Applicability Domain Ceiling
- Old Vs New
- Artifact
- Scaler
- Scaler
- Contract
- 070 Qa Protocol What
- Metadata
- Target
- 088 Group Aware Nested
- Evaluate
- 005 Gate Harness Prd
- Hydride Domain Grounding
- 091 The Prediction Record
- Report
- Build Element Tables
- Model
- 081 App Chart Vocabulary
- Manifest
- Metadata
- 061 Element Subset Outer
- 076 Predict Capacity Over
- 035 Contextmd Domain Glossary
- 034 Train And Publish
- 087 Canonical Composition Key
- Report
- Inverse Design Methods
- Inverse Design Methods
- Store
- Select
- 006 Ci Fast Lane
- 086 Gate Hg 4
- Inverse Design Methods
- Tooling
- Check Database
- 001 Pin And Lock
- 030 Leave One Alloy
- 033 Gate Ac 4
- Report
- Spike Feature Provenance
- Waiver Scope
- Scaler
- Selection
- 023 Scaler Fit Once
- 044 Screen Interface A
- Check Freeze
- Predict
- Validation
- 009 Raw Loaders With
- Evaluate
- Selection
- 012 Re Join Alloy
- Composites
- Canonical
- 008 Provenance Spike Resolve
- 010 Keyed Merge Replacing
- 073 End To End
- Metadata
- Readme
- 069 Infrastructure Pytest Ruff
- Inverse Design Methods
- Element Data
- Loco
- Scaler
- Refusals
- Hg2 Refusal Path
- Comparison
- 030 Leave One Alloy
- Scaler
- 015 Data Layer Golden
- 022 Featurisation Throughput Benchmark
- Canonical
- Target
- Manifest
- Manifest
- Manifest
- Init
- Refusals
- Init
- Init
- Init
- Init
- Protocol
- Init
- Init
- 024 Port Feature Selection
- Pyproject

## God Nodes (most connected - your core abstractions)
1. `load()` - 184 edges
2. `Config` - 148 edges
3. `_fixture()` - 105 edges
4. `featurize()` - 97 edges
5. `ScreenError` - 85 edges
6. `parse_formula()` - 80 edges
7. `ContractError` - 73 edges
8. `ModelSettings` - 69 edges
9. `FeatureContract` - 67 edges
10. `load_hydride_data()` - 62 edges

## Surprising Connections (you probably didn't know these)
- `One parser, not three — pymatgen is available and still declined` --references--> `group_keys()`  [EXTRACTED]
  kanban-hardening/020-featurize-the-descriptor-layers-public-interface.md → hydms/data/canonical.py
- `A group-disjoint calibration carve from train, never from val or test` --references--> `group_keys()`  [INFERRED]
  kanban-hardening/027-mapie-conformal-calibration.md → hydms/data/canonical.py
- `Two prediction spaces; the public one is weight percent` --conceptually_related_to--> `to_model_space()`  [INFERRED]
  kanban-hardening/028-predict-the-surrogates-public-interface.md → hydms/data/target.py
- `FeatureContract` --implements--> `Computability is recorded per composition, not per feature`  [EXTRACTED]
  hydms/descriptors/contract.py → kanban-hardening/019-the-22-feature-contract.md
- `Card 19: The 22-feature contract` --references--> `assert_contract()`  [EXTRACTED]
  kanban-hardening/019-the-22-feature-contract.md → hydms/descriptors/contract.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Screen suite composed by the evaluator** — kanban_045_family_stoichiometry_screen_ab2_ab5_family_stoichiometry, kanban_046_valence_electron_concentration_window_screen_vec_window, kanban_047_atomic_size_mismatch_screens_size_mismatch_criteria, kanban_050_cost_and_supply_risk_screen_hhi, kanban_051_the_evaluator_candidates_in_full_evaluation_table_out_evaluate [EXTRACTED 1.00]
- **Architecture A screen-and-rank pipeline (propose, evaluate, rank, write, gate)** — kanban_052_the_proposer_seam_proposer, kanban_053_enumerate_proposer_stoichiometry_grid_over_the_simplex_enumerate, kanban_051_the_evaluator_candidates_in_full_evaluation_table_out_evaluate, kanban_054_lower_confidence_bound_ranking_lcb_ranking, kanban_055_screening_cli_entry_point_search_run, kanban_057_ranked_candidate_output_schema_and_writer_ac_7, kanban_056_gate_ac_8_guard_rail_strength_on_the_top_20_ac_8 [EXTRACTED 1.00]
- **Phase T thermodynamics chain (load, parameterise, train, sanity-check, apply, benchmark)** — kanban_038_ml_hydpark_thermodynamic_loader_card, kanban_039_parameterise_surrogate_training_by_target_card, kanban_040_train_the_enthalpy_and_entropy_surrogates_card, kanban_041_gate_ac_5_predicted_entropy_clusters_near_130_j_mol_h2_k_card, kanban_042_van_t_hoff_module_card, kanban_043_benchmark_against_witman_et_als_published_results_card [EXTRACTED 1.00]
- **Phase B evidence chain: subsets swept, converged, seed-stable, explored and figured** — kanban_061_element_subset_outer_loop_element_subset_outer_loop, kanban_062_hypervolume_convergence_study_hypervolume_convergence_study, kanban_063_multi_seed_stability_study_multi_seed_stability_study, kanban_066_streamlit_pareto_front_explorer_pareto_front_explorer, kanban_067_thesis_figure_set_thesis_figure_set [EXTRACTED 1.00]
- **L0 Foundation: environment, package, config, artifact store, gates, CI** — kanban_hardening_001_pin_and_lock_the_project_conda_environment_pin_project_env, kanban_hardening_002_scaffold_the_hydms_package_with_pyproject_and_gpl_30_licence_scaffold_hydms, kanban_hardening_003_config_loader_relative_paths_seeds_and_thresholds_in_one_pla_config_loader, kanban_hardening_004_artifact_store_and_manifest_contract_artifact_store, kanban_hardening_005_gate_harness_prd_acceptance_criteria_as_runnable_checks_gate_harness, kanban_hardening_006_ci_fast_lane_lint_tests_and_gates_on_cached_artifacts_ci_fast_lane, kanban_hardening_007_ci_slow_lane_full_retrain_artifact_upload_and_version_promot_ci_slow_lane [EXTRACTED 1.00]
- **The silent-misalignment defect family found across the data layer** — kanban_hardening_010_keyed_merge_replacing_the_positional_concat_leak_l9, kanban_hardening_010_keyed_merge_replacing_the_positional_concat_duplicated_column_silently_dropped, kanban_hardening_011_target_transform_module_compute_never_join, kanban_hardening_012_re_join_alloy_class_on_formula_temperature_duplicated_in_concat, kanban_hardening_012_re_join_alloy_class_on_formula_leak_l8_canonical_key [INFERRED 0.85]
- **The Phase H leak inventory addressed by these cards (L3, L6, L8, L10, L11, L12, L1/L5)** — kanban_hardening_013_stratified_unique_formula_splits_seeded_and_reproducible_leak_l8, kanban_hardening_014_cleanlab_screening_as_a_data_layer_stage_leak_l3, kanban_hardening_014_cleanlab_screening_as_a_data_layer_stage_leak_l10, kanban_hardening_014_cleanlab_screening_as_a_data_layer_stage_leak_l12, kanban_hardening_024_port_feature_selection_inside_the_folds_reading_cleanlab_leak_l6, kanban_hardening_026_catboost_multiquantile_with_honest_early_stopping_leaks_l1_l5, kanban_hardening_029_evaluation_metrics_with_bootstrap_confidence_intervals_leak_l11 [INFERRED 0.85]
- **The descriptor layer's featurisation path: parse, table lookup, statistic, composite, contract** — hydms_data_load_parse_formula, hydms_descriptors_element_data_require_coverage, hydms_descriptors_stats_statistics, hydms_descriptors_composites_decompose, hydms_descriptors_contract_assert_contract, hydms_descriptors_featurize_featurize [EXTRACTED 1.00]
- **Store the fitted result as a number, never a pickled estimator** — kanban_hardening_023_scaler_fit_once_persist_never_refit_result_not_estimator, kanban_hardening_023_scaler_fit_once_persist_never_refit_fittedscaler, kanban_hardening_027_mapie_conformal_calibration_correction_constant, kanban_hardening_019_the_22_feature_contract_order_is_a_declaration [INFERRED 0.85]
- **The refusal path: screen protocol, screens, contract, delivery and the gate** — kanban_hardening_044_screen_interface_a_verdict_with_a_reason_never_a_silent_drop_screen_protocol, kanban_hardening_048_applicability_domain_ceiling_above_physical_ceiling, kanban_hardening_049_element_movers_distance_novelty_screen_novelty_not_domain, kanban_hardening_075_delivery_contract_request_result_and_refusal_schemas_reason_codes, kanban_hardening_076_predict_capacity_over_an_immutable_artifact_bundle_resolve, kanban_hardening_077_gate_hg_2_the_refusal_path_never_a_bare_number_refusals_doc [EXTRACTED 1.00]
- **The Phase H gate registry that promotion demands** — kanban_hardening_033_gate_ac_4_known_alloys_round_trip_through_predict_card, kanban_hardening_071_gate_hg_1_leak_sentinels_one_test_per_named_leak_card, kanban_hardening_077_gate_hg_2_the_refusal_path_never_a_bare_number_card, kanban_hardening_079_gate_hg_3_api_contract_tests_and_transport_parity_card, kanban_hardening_034_train_and_publish_the_deployed_artifact_version_promote [EXTRACTED 1.00]
- **The --emit pattern: a generated file whose committed bytes a test asserts** — kanban_hardening_048_applicability_domain_ceiling_domain_reference, kanban_hardening_049_element_movers_distance_novelty_screen_novelty_reference, kanban_hardening_073_end_to_end_smoke_pipeline_on_a_sampled_fixture_fixture, kanban_hardening_077_gate_hg_2_the_refusal_path_never_a_bare_number_refusals_doc [INFERRED 0.95]
- **The five-chart vocabulary that resists false belief** — kanban_hardening_081_app_chart_vocabulary_charts_that_resist_false_belief_prediction_band, kanban_hardening_081_app_chart_vocabulary_charts_that_resist_false_belief_domain_strip, kanban_hardening_081_app_chart_vocabulary_charts_that_resist_false_belief_temperature_sweep, kanban_hardening_081_app_chart_vocabulary_charts_that_resist_false_belief_nearest_neighbours_chart, kanban_hardening_081_app_chart_vocabulary_charts_that_resist_false_belief_parity_plot [EXTRACTED 1.00]
- **The delivery seam: one prediction path, one set of guard rails** — kanban_hardening_082_streamlit_forward_prediction_page_app_is_an_http_client, kanban_hardening_085_adr_the_delivery_seam_and_why_the_api_owns_no_ml_logic_library_owns_no_io, kanban_hardening_091_the_prediction_record_and_replay_prediction_record, kanban_hardening_091_the_prediction_record_and_replay_replay, kanban_hardening_085_adr_the_delivery_seam_and_why_the_api_owns_no_ml_logic_assembly_order [INFERRED 0.85]
- **Generated documents rebuilt by --emit and pinned by a byte-identity test** — kanban_hardening_090_the_refusal_catalogue_docs_refusals_md, reports_loco_loco_report, reports_model_evaluation_report, reports_feature_selection_old_vs_new_report [EXTRACTED 1.00]
- **Physical Interpretation Descriptor Set** — report_avg_valence_d, report_avg_is_alkaline, report_avg_polzbl_divi_atom_mass, report_dev_zunger_radii_sum, report_temperature_k [EXTRACTED 1.00]
- **HydMS Ordered Pipeline Stages** — machine_model_src_merge_datasets, machine_model_src_log_transform_target, machine_model_src_extract_features_cbfv, machine_model_src_cleanlab, machine_model_src_boruta_feateng, machine_model_src_feature_selection, machine_model_src_split_data, machine_model_src_benchmark_model_selection, machine_model_src_catboostmodel [EXTRACTED 1.00]
- **Inverse-Design Guard Rail Stack** — research_inverse_design_methods_uncertainty_quantification, research_inverse_design_methods_applicability_domain, research_inverse_design_methods_physics_filters, research_inverse_design_methods_novelty_check, research_inverse_design_methods_lower_confidence_bound_ranking, research_inverse_design_methods_enumerate_and_screen [EXTRACTED 1.00]

## Communities (172 total, 15 thin omitted)

### Community 0 - "Featuriser Element Tables"
Cohesion: 0.03
Nodes (106): PropertyTable, The numeric element properties, and where each one came from. Card #16. This…, One element-property table, read once and never mutated. Frozen because a table…, A table from an in-memory ``{element: {property: value}}`` mapping. The…, Whether a real number can be produced, with no exception and no judgement., property -> the elements carrying it, built once on first use. Derived, so…, Every element this table can supply ``prop`` for. Membership answers both…, _audit_composites() (+98 more)

### Community 1 - "Prediction Request Path"
Cohesion: 0.04
Nodes (103): PredictionRequest, What a caller asks: one composition at one temperature. Deliberately the…, L6 — the boundary users meet: one prediction path, and the vocabulary it…, ArtifactBundle, bundle_from(), _candidate(), _check_columns(), clear_cache() (+95 more)

### Community 2 - "Delivery Refusal Vocabulary"
Cohesion: 0.04
Nodes (102): delivery_screens(), Novelty, The screens the delivery path runs, in the order their verdicts are reported.…, Every code an answer may carry: admitted, the screens' declared reasons,…, The one code and the one sentence a caller receives, from every screen that…, How far this composition is from the nearest alloy the model was trained on.…, reason_codes(), resolve() (+94 more)

### Community 3 - "Leak Sentinels"
Cohesion: 0.04
Nodes (95): _baseline_error(), _baseline_prediction(), _class_frame(), _deployed_fit(), _drop_object_columns(), _explainability_record(), _explanation(), _features() (+87 more)

### Community 4 - "Canonical Composition Key"
Cohesion: 0.04
Nodes (91): alloy_class_table(), alloy_classes(), canonical_key(), CanonicalisationError, group_keys(), _named(), DataFrame, Series (+83 more)

### Community 5 - "Descriptor Feature Contract"
Cohesion: 0.03
Nodes (81): assert_contract(), ContractError, FeatureSpec, DataFrame, ValueError, A feature matrix, a name or a manifest does not match the contract. A…, One column: what it is called, and what it is made of. Frozen, like every other…, Whether this column is carried from the raw input rather than computed. Exactly… (+73 more)

### Community 6 - "Keyed Feature Merge"
Cohesion: 0.06
Nodes (86): _addressed(), FeatureBlock, merge_features(), MergeError, _named(), _null_mask(), Any, DataFrame (+78 more)

### Community 7 - "External Libraries and Archival Report"
Cohesion: 0.05
Nodes (69): boruta, catboost, cbfv.composition, cleanlab.regression.learn, joblib, Machine_Model Pipeline Guide, SHAP Interpretation Limitations, Split Data Summary (+61 more)

### Community 8 - "Element Mover's Distance Novelty"
Cohesion: 0.05
Nodes (79): distances(), ElementMoversDistance, novelty_screen(), NoveltyReference, Parse formulas onto the modified-Pettifor scale, one row each. Each…, Nearest known composition for every candidate, batched. Implements ElMD's…, The known chemistry a candidate is measured against, and the bound it may not…, The reference as the committed file, sparse and deterministic. Sparse because a… (+71 more)

### Community 9 - "Surrogate Prediction Interface"
Cohesion: 0.04
Nodes (78): clear_cache(), _empty_intervals(), load_surrogate(), predict(), PredictionError, Any, DataFrame, Index (+70 more)

### Community 10 - "Feature Selection Inside Folds"
Cohesion: 0.07
Nodes (75): ValueError, The selector cannot run on what it was given, and the message says why. A…, Choose the feature set, from ``train`` and from nothing else. The three…, Run the selector once per outer fold of card #88's protocol. The protocol shape…, select_across_folds(), select_features(), SelectionError, alloys() (+67 more)

### Community 11 - "Smoke Pipeline Fixture"
Cohesion: 0.04
Nodes (71): FixtureRequest, check_fixture(), _elapsed(), emit(), fixture_schema(), load_fixture(), main(), _parser() (+63 more)

### Community 12 - "Screen Protocol Runner"
Cohesion: 0.07
Nodes (62): apply_screens(), ValueError, A screen broke the contract, or the runner was given something it cannot…, Run every screen over the whole batch and collect one verdict table. Args:…, ScreenError, frame(), Three candidate features. Only `f1` survives on the training rows alone. `f2`…, batch() (+54 more)

### Community 13 - "Delivery Contract Types"
Cohesion: 0.05
Nodes (67): answer_from(), DomainVerdict, PredictionResult, Answer, One screen's answer about this candidate, carried verbatim into the result. The…, Whether this candidate is one the model may be asked about, and why. The second…, The admitted verdict, with one passing :class:`ScreenVerdict` per named screen.…, An answer with a number in it -- and therefore with an interval and a verdict.… (+59 more)

### Community 14 - "Quantile Model Fitting"
Cohesion: 0.06
Nodes (63): L3 — model choice, the fit-once scaler, quantile regression and conformal…, _columns(), final_fit(), fit_quantile_model(), _FoldRows, Hyperparameter, loss_function(), model_from() (+55 more)

### Community 15 - "Leak Inventory"
Cohesion: 0.04
Nodes (64): L0 -- the leak sentinels: the guarantee that a leak this phase removed stays…, by_id(), Leak, The thirteen named leaks, as data. ``docs/PHASE-H-RUNBOOK.md`` section 1 is the…, Look one leak up by its id. Raises: KeyError: No such leak. Loud on purpose: a…, One row of the runbook's leak inventory. Attributes: id: ``"L1"`` .. ``"L13"``.…, audit(), Deferral (+56 more)

### Community 16 - "Raw Data Loaders"
Cohesion: 0.07
Nodes (61): _check_value(), ColumnSpec, hydride_data_schema(), _load(), load_ml_hydpark(), load_prefeaturized(), ml_hydpark_schema(), _named() (+53 more)

### Community 17 - "Descriptor Computability"
Cohesion: 0.04
Nodes (46): Computability, FeatureContract, Hole, _named(), Any, The 22 features: their names, their order, their dtype, and where each one is…, Render offenders for a message: in the order given, truncated, and counted., Every element ``table`` can supply ``prop`` for. A one-line forward to… (+38 more)

### Community 18 - "Gate Harness Registry"
Cohesion: 0.06
Nodes (59): argparse, Every registered gate, ordered by name. Discovery happens once per process., Choose gates by name, by lane, or take them all. Raises: UnknownGate: A…, Execute the given gates and collect their results. No gate can end this call…, registry(), run(), select(), The human-readable run: a table, a summary, and the detail behind any red row.… (+51 more)

### Community 19 - "Conformal Calibration"
Cohesion: 0.06
Nodes (61): calibration_groups(), calibration_slice(), conformal_from(), ConformalError, Hashable, ValueError, The calibration cannot be fitted, or is being applied to the wrong prediction.…, Split training rows into the rows the model grows on and the rows that… (+53 more)

### Community 20 - "Artifact Manifest"
Cohesion: 0.07
Nodes (49): _distribution_version(), environment(), Git, ManifestError, now(), PayloadRecord, Any, ValueError (+41 more)

### Community 21 - "Surrogate Training Run"
Cohesion: 0.06
Nodes (54): emit(), Measure the reference from the curated data. The slow half of this module.…, capacity_contender(), capacity_matrix(), Configuration, ModelSettings, What one outer fold's search settled on, and what it cost to find out. Stored…, One row of the chosen-hyperparameter table. (+46 more)

### Community 22 - "Calibrated Quantile Heads"
Cohesion: 0.06
Nodes (45): _coverage(), DataFrame, Raw against calibrated, over the calibration rows, in weight percent. Both…, _assert_parity(), calibrated_heads(), compare_metrics(), _extract_correction(), fit_conformal() (+37 more)

### Community 23 - "Applicability Domain Screen"
Cohesion: 0.06
Nodes (53): ApplicabilityDomain, The applicability-domain ceiling, as a :class:`~hydms.screens.protocol.Screen`.…, Every code this screen can emit. Five rejections and the shared indeterminate., The capacity level above which the corpus holds one family. Weight percent., candidates(), DataFrame, parametrize, L4 -- the applicability-domain ceiling. Card #48. ``docs/QA-PROTOCOL.md`` names… (+45 more)

### Community 24 - "Artifact Store Promotion"
Cohesion: 0.10
Nodes (51): Manifest, Everything recorded beside one artifact version. Constructed by…, current(), load(), promote(), The promoted version, or ``None`` if nothing has been promoted yet., Point ``current`` at ``version``, refusing anything its gates did not…, Read one version's manifest without loading anything it points at. Separate… (+43 more)

### Community 25 - "Grouped Data Splits"
Cohesion: 0.07
Nodes (49): The train/val/test protocol. Fractions are 0.20 / 0.10 as `split_data.py`…, Split, assign_splits(), _cut(), _group_statistics(), _merge_rare_strata(), Any, DataFrame (+41 more)

### Community 26 - "Gate CLI Reporting"
Cohesion: 0.06
Nodes (45): GateReport, Any, LookupError, The outcome of one harness run, and the object card #4's manifest embeds., Whether this run may be called green. A skip is tolerated under a broad…, A gate was requested by a name nothing is registered under., UnknownGate, _list() (+37 more)

### Community 27 - "Acceptance Criteria Gates"
Cohesion: 0.07
Nodes (35): AC-1 -- the same seed reproduces identical metrics. PRD section 10.1: the…, The gate. It fits two models and compares what they are worth, never their…, SeedReproducibility, AC-3 -- conformal interval coverage matches its nominal level. PRD section…, AC-4 -- known training alloys round-trip through the screening path. PRD…, AC-5 -- predicted entropy clusters near -130 J/(mol H2 K). PRD section 10.5.…, AC-7 -- no candidate is published without both an ElMD distance and an interval…, AC-8 -- at least half the top 20 candidates sit inside the guard rails. PRD… (+27 more)

### Community 28 - "Comparison"
Cohesion: 0.07
Nodes (24): Comparison, _features(), _markdown(), DataFrame, The published 22 against the set this project now declares, and what the change…, The ``features`` cell of a selection table, back as names., A GitHub table from a frame, without taking a dependency on ``tabulate``. The…, ``5`` as ``five``, and anything larger as itself. (+16 more)

### Community 29 - "Comparison"
Cohesion: 0.06
Nodes (48): date, ComparisonError, placeholder_exposure(), Path, Series, ValueError, A comparison was asked for that the tables on disk cannot support. A…, The curated formula column. Loaded once per comparison, never per feature. (+40 more)

### Community 30 - "Contract"
Cohesion: 0.08
Nodes (29): _code(), ContractError, _finite(), _named(), Any, ValueError, L6 -- the vocabulary every consumer of a prediction speaks. Three consumers are…, An answer cannot be built, or a payload is not one. A ``ValueError``, like… (+21 more)

### Community 31 - "Ac3 Conformal Coverage"
Cohesion: 0.06
Nodes (34): _band(), ConformalCoverage, _coverage(), DataFrame, ndarray, Series, The names of the outer two heads, taken from the correction that widened them.…, The share of observations the band contains, inclusive at both ends. (+26 more)

### Community 32 - "Config"
Cohesion: 0.07
Nodes (48): load(), Load, validate and return the configuration. Args: path: A YAML file. Defaults…, Locate the repository root for this checkout. Resolution order, most explicit…, repo_root(), cfg(), MonkeyPatch, parametrize, Path (+40 more)

### Community 33 - "Load"
Cohesion: 0.05
Nodes (46): _fractions(), How close the key came to merging two materials that are not the same one.…, Measure how much room the key had, over a whole corpus. Rounding is a decision…, Separation, FormulaError, load_hydride_data(), parse_formula(), A composition string is not a formula this project will accept. Distinct from… (+38 more)

### Community 34 - "Benchmark"
Cohesion: 0.06
Nodes (39): _best(), candidates(), machine(), main(), measure(), Measurement, How many candidate compositions this layer can featurise per second, and where…, The fraction of the wall clock spent in Python parsing formula strings. (+31 more)

### Community 35 - "Loco"
Cohesion: 0.07
Nodes (48): _direction(), document(), _or_absent(), The two averages, the count behind each, and the random-split number beside…, The published write-up, built from the tables and never typed. Generated rather…, A number, or a phrase -- never the string ``nan``. ``summary`` writes NaN when…, Which way the support-weighted mean falls, measured rather than predicted. A…, summary() (+40 more)

### Community 36 - "Element Data"
Cohesion: 0.07
Nodes (47): ElementDataError, load_table(), Path, ValueError, Load one of :data:`TABLES` by name. Cached: the CSVs never change at runtime., Raise unless ``table`` can supply every one of ``properties`` for every…, An element property was asked for and the table cannot honestly supply it. A…, _read() (+39 more)

### Community 37 - "Stats"
Cohesion: 0.05
Nodes (46): CompositionError, ValueError, A batch of compositions cannot yield a statistic, and the message says why. A…, _cbfv_oliynyk(), oliynyk_reference(), pack(), ndarray, parametrize (+38 more)

### Community 38 - "Ac2 Parity"
Cohesion: 0.05
Nodes (44): Config, The whole configuration. Immutable, validated, with absolute paths., cbfv(), cfg(), passing(), _perturbed(), MonkeyPatch, Card #21 — the parity gate, and the four things it has to get right. 1. **It… (+36 more)

### Community 39 - "Validation"
Cohesion: 0.07
Nodes (37): _assemble(), _averaged(), _complete(), _discard(), Fold, FoldSet, _keeper(), leave_one_class_out() (+29 more)

### Community 40 - "059 Pymoo Problem Definition"
Cohesion: 0.07
Nodes (47): Card 38: ML-HydPARK thermodynamic loader, ML-HYDPARK v0.0.5 thermodynamic subset (772 complete rows, 744 formulae), Card 39: Parameterise surrogate training by target, Target as a config key, not a second training script, Card 40: Train the enthalpy and entropy surrogates, Witman et al. pretrained thermodynamic models (rejected as a dependency), Card 41: GATE AC-5 — predicted entropy clusters near -130 J/(mol H2 K), ΔS ≈ -130 J/(mol H2 K) physics invariant (+39 more)

### Community 41 - "Model"
Cohesion: 0.07
Nodes (44): column_names(), quantile_metrics(), What one fit's predictions are worth, in weight percent. All of it in weight…, The column name for each quantile: ``("q0.1", "q0.5", "q0.9")``. The one place…, The names :meth:`predict` returns, in order., The comparison the card warns against, performed once so the warning is a…, test_the_raw_heads_would_have_failed_this_gate_on_a_working_pipeline(), The card's whole claim, measured. On the calibration rows the calibrated… (+36 more)

### Community 42 - "Evaluate"
Cohesion: 0.08
Nodes (44): datetime, _asserted(), _bootstrap(), _format(), _headline(), _heads(), Interval, pdp_table() (+36 more)

### Community 43 - "L3 L10 Holdout Immutability"
Cohesion: 0.08
Nodes (41): assert_holdout_unchanged(), _fingerprint(), _named(), Any, Hashable, The mechanical guards behind the leak sentinels. Eight functions, each…, Select ``labels`` from ``table``, refusing a duplicated label. A duplicated…, Every held-out row must survive a stage byte-identical. Guards **L3**… (+33 more)

### Community 44 - "Composites"
Cohesion: 0.09
Nodes (38): Composite, composite_properties(), CompositeError, decompose(), Disagreement, disagreements(), ValueError, How two element properties combine into one derived property -- and who did the… (+30 more)

### Community 45 - "Validation"
Cohesion: 0.08
Nodes (41): alloys(), _folds(), Any, DataFrame, L3 -- the folds group on the material, and nothing scores on what it was chosen…, A split assignment that holds the last twenty rows out, so `nested_scores` will…, The real 1,279 rows and card #13's split assignment, computed once., `grouped_folds` with the fixture's bin counts, so a test says only what it… (+33 more)

### Community 46 - "Window"
Cohesion: 0.07
Nodes (36): _number(), DataFrame, Two codes: outside the interval, and no number to compare., The interval as it appears in every reason this screen writes., A verdict per candidate: inside, outside, or unreadable. Raises: ScreenError:…, The trained temperature range, from config -- the outer bound of the refusal…, A bound or a value as it should read in a sentence: 773, not 773.0; 313.5 stays., Admit a candidate when ``column`` lies within ``[low, high]``. Attributes:… (+28 more)

### Community 47 - "Promote"
Cohesion: 0.12
Nodes (40): main(), _parser(), ArgumentParser, TextIO, Path, Card #34 — certifying a candidate version, and refusing to when it is not…, Two hops from a promoted model to the commit that fitted it, neither inferred., Recorded as a test because it is the finding, not a limitation of the command.… (+32 more)

### Community 48 - "Clean"
Cohesion: 0.08
Nodes (34): MALFORMED_FORMULAE, Drop suspect **training** rows, and report every finding on every split. Args:…, screen(), Mg0853Ni0.125La0.022 — the missing decimal point, DEPLOYED_SCREENING — what the pipeline actually removes (893/873/20/18), A golden test's real failure mode is silence, hydride(), DataFrame (+26 more)

### Community 49 - "Ac3 Coverage"
Cohesion: 0.06
Nodes (34): The binomial standard error of a coverage estimate over ``n`` independent rows.…, _standard_error(), pointed_at(), Path, A factory: save a :class:`~hydms.surrogate.deploy.DeployedFit`, get a…, parametrize, Path, Card #31 — the coverage gate, and the four things it has to get right. 1. **It… (+26 more)

### Community 50 - "Hg2 Refusal Path"
Cohesion: 0.07
Nodes (36): Answered, _not_always(), Probe, _probes(), Any, Enum, str, HG-2 -- no prediction path returns a bare number, and every refusal says which… (+28 more)

### Community 51 - "Selection"
Cohesion: 0.08
Nodes (36): _boruta(), _candidates(), _factor(), _named(), Any, DataFrame, Hashable, Series (+28 more)

### Community 52 - "Validation"
Cohesion: 0.14
Nodes (38): Contender, grouped_folds(), nested_scores(), SplitSettings, ``StratifiedGroupKFold`` over the canonical compositions of ``frame``. The…, Everything the hyperparameter search is allowed to see, and nothing else.…, The one fit that is scored: refit on the outer fold's training rows, scored on…, One model in the comparison: how it is tuned, and how it is scored. Two… (+30 more)

### Community 53 - "Metadata"
Cohesion: 0.09
Nodes (31): MetadataError, ValueError, Metadata is missing where it is needed, or present where it must not be. A…, The record and the feature matrix, side by side, joined by **label**. The other…, with_features(), parametrize, L1 -- the metadata boundary, and the alloy class that has to cross it. Card…, ``Ce1Mg12`` is ``MIC`` in the file and ``Mg12Ce1`` is ``Mg``. A fold that holds… (+23 more)

### Community 54 - "Deploy"
Cohesion: 0.11
Nodes (32): _cost(), _destination(), main(), _parser(), ArgumentParser, Path, TextIO, Calibrate the deployed fit's band, and report what the calibration bought.… (+24 more)

### Community 55 - "Protocol"
Cohesion: 0.09
Nodes (26): L4 — physics windows, the applicability-domain ceiling, novelty and cost. A…, _check_screen(), _check_verdict(), _column(), _fingerprint(), _named(), Any, DataFrame (+18 more)

### Community 56 - "Novelty"
Cohesion: 0.07
Nodes (31): float64, _elmd_class(), emit(), main(), _named(), _number(), Any, DataFrame (+23 more)

### Community 57 - "Store"
Cohesion: 0.11
Nodes (35): Every complete artifact version, oldest first. A directory with no…, Write a new artifact version and return the manifest recorded beside it. Args:…, save(), versions(), contract(), green(), Any, A string sort puts v10 before v9 and promotes the wrong artifact on the tenth… (+27 more)

### Community 58 - "L7 L8 Grouping"
Cohesion: 0.08
Nodes (34): assert_disjoint_groups(), No group key may appear in more than one partition. Guards **L8**…, _l2_live(), _l4_live(), _l7_a_formula_in_two_folds(), _l7_folds_grouped_by_composition(), _l7_live(), _l8_one_composition_in_two_splits() (+26 more)

### Community 59 - "Domain"
Cohesion: 0.07
Nodes (29): applicability_domain(), DomainReference, main(), _number(), DataFrame, Index, ndarray, Series (+21 more)

### Community 60 - "Metamorphic"
Cohesion: 0.09
Nodes (34): TempPathFactory, _features(), DataFrame, ndarray, parametrize, Relations between two related inputs, where no oracle exists. There is no…, Catches: a featuriser that reads the formula string positionally. `Ce1Mg12` and…, Catches: a prediction path that keys, caches or dispatches on the raw formula… (+26 more)

### Community 61 - "Store"
Cohesion: 0.10
Nodes (32): Exception, L0 — the versioned artifact store and its manifest. The only way a model,…, ArtifactError, Base for every refusal from :mod:`hydms.artifacts`., _check_waivers(), GatesIncomplete, PayloadCorrupt, LookupError (+24 more)

### Community 62 - "Target"
Cohesion: 0.11
Nodes (33): Weight percent to the space the surrogate is fitted in: ``log1p``. ::…, Model space back to weight percent: ``expm1``. **A negative result is returned,…, to_model_space(), to_wt_pct(), Two prediction spaces; the public one is weight percent, parametrize, L1 -- the target transform and the two spaces it moves between. Card #11. Four…, The data covers its range unevenly; a sweep covers it evenly, including the… (+25 more)

### Community 63 - "Ac6 Loco"
Cohesion: 0.15
Nodes (29): str, The four things a gate run can honestly say. ``SKIPPED`` is not a mild pass. It…, Status, _config(), Path, AC-6 — that the extrapolation number is published beside the interpolation one.…, A probe's tables are the same shape as a real run's, so committed probe numbers…, The mistake this gate exists to catch, and the only one a person could make… (+21 more)

### Community 64 - "L2 L4 Model Selection"
Cohesion: 0.12
Nodes (28): assert_selection_is_nested(), What one candidate model contributed to the model-selection decision. Card…, Model selection may not see a held-out metric, nor score on the folds it tuned…, SelectionRecord, _l2_record_without_a_test_metric(), _l2_test_metric_in_the_record(), _l4_nested_folds(), _l4_tuned_and_scored_on_the_same_fold() (+20 more)

### Community 65 - "Ac4 Round Trip"
Cohesion: 0.10
Nodes (24): _features(), Any, DataFrame, Hashable, Series, ``wanted`` rows the model grew on, taken from as many alloy classes as…, Per-feature values from both paths, for the card's "diagnosable" box. Computed…, _spread() (+16 more)

### Community 66 - "L1 L5 Early Stopping"
Cohesion: 0.10
Nodes (27): assert_early_stopping_is_honest(), The rows that choose the stopping iteration may not be the rows that score it.…, _l1_empty_eval_set(), _l1_eval_set_is_the_test_pool(), _l1_eval_set_is_the_validation_split(), _l5_fold_stops_on_an_inner_slice(), _l5_fold_stops_on_itself(), `Catboostmodel.py:604-606` -- final_model.fit(..., eval_set=test_pool). (+19 more)

### Community 67 - "L12 Sample Weights"
Cohesion: 0.13
Nodes (27): assert_weights_ignore_target(), Sample weights may be computed from the rows' features; never from their…, _frame(), DataFrame, leak, L12 -- a row may not be weighted by its own answer.…, The case the rescale exists for, and the one a shuffle alone cannot see. Every…, A check against a column that is not there passes vacuously, which is the… (+19 more)

### Community 68 - "Screening"
Cohesion: 0.10
Nodes (23): Finding, label_issues(), LabelIssues, _named(), DataFrame, Series, ValueError, L1 -- which **training** rows are suspect, and the record of what was removed.… (+15 more)

### Community 69 - "L9 Keyed Merge"
Cohesion: 0.14
Nodes (26): assert_merge_is_keyed(), A merge must join on a key, not on row position. Guards **L9**…, frames(), keyed_join(), positional_concat(), Any, DataFrame, L9 -- the merge joins on a key, or it silently attaches features to the wrong… (+18 more)

### Community 70 - "Evaluate"
Cohesion: 0.11
Nodes (26): EvaluationError, main(), _parser(), ArgumentParser, Path, TextIO, ValueError, Read the tables, put an interval on every number, and report. Returns the exit… (+18 more)

### Community 71 - "Loco"
Cohesion: 0.13
Nodes (26): _budget(), _chosen(), _destination(), _emit(), _extreme(), main(), _parser(), ArgumentParser (+18 more)

### Community 72 - "Conftest"
Cohesion: 0.10
Nodes (26): hydride_raw(), known_collisions(), Path, Shared fixtures for the hydms test suite. Two rules shape this file: -…, The repository root, so no test needs a relative path or a `cwd` assumption., Path to the raw dataset, skipping the test if it is not in this checkout., The raw dataset, read once per session. Private: use `hydride_raw` for a safe…, A fresh copy of the raw dataset (1279 x 6), safe to mutate. Columns:… (+18 more)

### Community 73 - "L11 Explainability"
Cohesion: 0.14
Nodes (25): assert_explanation_is_not_held_out(), LeakDetected, An explainability record must say what it ran on, and it must not be a held-out…, A named leak from the Phase H inventory is present. An ``AssertionError``…, DataFrame, leak, L11 -- an explanation of a model may not be computed on the rows it is scored…, The corrected twin. A detector that rejects the fix is one nobody can satisfy. (+17 more)

### Community 74 - "L13 Class Survival"
Cohesion: 0.15
Nodes (25): assert_metadata_survives(), A stage may add columns and compute features; it may not lose the ones it was…, _l13_live(), Card #12's join, against the real dataset: the class arrives on the other side.…, archival_featurisation(), honest_featurisation(), DataFrame, L13 -- a column that is not a feature is still not disposable.… (+17 more)

### Community 75 - "Scaler"
Cohesion: 0.12
Nodes (26): fit_scaler(), Series, Fit the scaling transform on one split of a feature matrix. The split is a…, Series, `refuse_non_features` runs at fit time, where the feature set is established., `temperature(K)` is a raw column and a feature; a positional concat returns it…, The fit only reads the training rows, so only those can stop it., `RobustScaler` substitutes 1.0 for a zero span, so 1.0 alone cannot be read… (+18 more)

### Community 76 - "Scaler"
Cohesion: 0.11
Nodes (24): FittedScaler, A fitted robust scaling transform, with no way to fit it again. Constructed…, How many features it scales., matrix(), DataFrame, parametrize, The AC-4 failure mode, closed: the caller's order does not reach the model., scikit-learn accepts one with a UserWarning; that is the door this closes. (+16 more)

### Community 77 - "016 Element Property Tables"
Cohesion: 0.10
Nodes (24): ndarray, The five statistics of one property over a batch of compositions. Every field…, ``stats["avg"]`` -- so the caller can index with the half of a feature name.…, The five statistics of one element property over a batch of compositions. Args:…, Statistics, scripts/build_element_tables.py — the derivation audit trail, Card 16: Element property tables with cited provenance, CBFV carries no licence and cannot be vendored (+16 more)

### Community 78 - "Golden"
Cohesion: 0.10
Nodes (24): diff(), measure_deployed_screening(), modelling_contract(), slow, L1 -- one pinned record of what the data layer produces. Card #15. Every other…, The 21-feature contract the modelling matrix is built from. ``COSTLY_FEATURE``…, Screen the training rows the way the fit does, and record what it removed. Not…, Every differing fact as a table, or an empty string when they agree. (+16 more)

### Community 79 - "Check Board"
Cohesion: 0.19
Nodes (22): Card, check_cards(), check_cycles(), check_freeze(), check_links(), freeze_in_force(), _int_list(), _int_or_none() (+14 more)

### Community 80 - "No Leak"
Cohesion: 0.15
Nodes (23): _frame(), DataFrame, The test split is named by every fit and read by none of them -- leaks L1 and…, `eval_set=test_pool`, reintroduced against the real fit. This is the…, Half the test set is not half a leak; the whole validation split or nothing., CatBoost refuses this at fit time; the point is that it refuses here first. The…, Cruder than L1, and not L1: a `ModelError`, so a raised `LeakDetected` always…, Early stopping that watches rows the trees are growing on never fires. Not in… (+15 more)

### Community 81 - "Init"
Cohesion: 0.10
Nodes (21): _build(), ConfigError, Conformal, Domain, Model, Paths, Any, Path (+13 more)

### Community 82 - "Ac1 Reproducibility"
Cohesion: 0.13
Nodes (20): _differences(), Any, Every number that moved, as ``(name, first, second, gap)``. The metrics *and*…, parametrize, slow, Card #32 — the reproducibility gate, and the decision it is built on. The…, A fit that stopped elsewhere and scored the same is reproducible by accident.…, ``r2`` is NaN when the truth has no variance, and NaN != NaN would report that… (+12 more)

### Community 83 - "L6 Selection Independence"
Cohesion: 0.16
Nodes (22): assert_selection_ignores_holdout(), Perturbing the held-out rows must not change the selected feature set. Guards…, Any, DataFrame, L6 -- feature selection must be blind to the rows it does not own.…, A failure a reviewer cannot reproduce is a failure that gets dismissed., The detector perturbs a copy. A detector that damages its input is used once., Nothing could be perturbed, so the check would pass whatever the selector does. (+14 more)

### Community 84 - "014 Cleanlab Screening As"
Cohesion: 0.11
Nodes (22): Card 13: Stratified unique-formula splits, seeded and reproducible, Leak L8: splits grouped on the raw formula string, Measured split 893 / 131 / 255 over 780 / 111 / 224 compositions, Three physically impossible curated rows (H/M above ceiling), Card 14: CleanLab screening as a data-layer stage, Leak L10: held-out features clipped by their own residuals, Leak L12: target-conditioned sample weights, Leak L3: held-out labels overwritten by the model's own predictions (+14 more)

### Community 85 - "048 Applicability Domain Ceiling"
Cohesion: 0.10
Nodes (22): CONTEXT.md domain glossary, Optimise in composition space; never invert descriptors, Chapter 1 revision: what exists, what was wrong, what it is now, Ranked composition-only future-work programme (Miedema, H/M, proxies, base learner), Decide the whole change set first; run LOCO once, Mg fails by construction: trees cannot predict above the trained range, Sloping PCT plateaus: pressure is the unobserved confounder, ABOVE_PHYSICAL_CEILING — a separate code from OUT_OF_DOMAIN (+14 more)

### Community 86 - "Old Vs New"
Cohesion: 0.13
Nodes (22): Card #83: Model-card page — honest metrics and stated limits, The per-row calibrated interval width distribution, The near-ambient temperature bin is the weakest, Three R² readings, and a sentence saying which is which, Card #89: REPORT.md versus the artifacts it cites, Eu1Ni5: a corrupted row in the published feature matrix, §4.2's Overfitting footnote mixes two target spaces, REPORT.md is preserved unedited, and why (+14 more)

### Community 87 - "Artifact"
Cohesion: 0.11
Nodes (18): Candidate, matrix(), NoCandidate, DataFrame, LookupError, Path, Series, Which artifact version a gate scores, and how it gets hold of it. Two gates --… (+10 more)

### Community 88 - "Scaler"
Cohesion: 0.12
Nodes (19): _declared_features(), _named(), L3 -- the scaling transform is fitted once, on the training split, and travels…, Render offenders for a message: sorted, truncated, and counted., The fitted scaler held in a loaded artifact version, checked against its…, The feature names the bundle's manifest records, or ``None`` if it records…, scaler_from(), Any (+11 more)

### Community 89 - "Scaler"
Cohesion: 0.17
Nodes (20): ValueError, The scaler cannot be fitted, or is being asked to transform the wrong matrix. A…, ScalerError, _fitted(), L3 -- the scaler is fitted once, on train, and can never be fitted again. Card…, The guard that stops "fit on train" from being satisfied by relabelling., Paired by label, never by position -- leak L9 in a new place., test_a_degenerate_name_that_is_not_a_feature_is_refused() (+12 more)

### Community 90 - "Contract"
Cohesion: 0.11
Nodes (17): Interval, A calibrated prediction interval, in weight percent, with the level it targets.…, ``upper - lower``, in :data:`UNIT`. Computed rather than stored, so it cannot…, Whether ``value`` lies inside the closed band., The interval as JSON-ready primitives, ``width`` included for a reader., parametrize, The refusal is on `Interval`, which is why the result's own cross-check never…, Cards #48 and #77 act on it; clipping here would hide what the band exists to… (+9 more)

### Community 91 - "070 Qa Protocol What"
Cohesion: 0.11
Nodes (20): Cross-check every formula with hydms.data.load.parse_formula, _dictify drops unknown symbols and keeps the rest — silent partial parse, A fixed guard kept its old reason: the refusal misnamed the mechanism, QA protocol: what must be tested at each layer, Four test kinds: golden, metamorphic, contract, sentinel, A gate that cannot go red is not a gate, docs/QA-PROTOCOL.md — the per-layer testing contract, GATE HG-1: leak sentinels, one test per named leak (+12 more)

### Community 92 - "Metadata"
Cohesion: 0.16
Nodes (18): Columns, The column names in the raw dataset, which are not identifiers and contain…, metadata_columns(), _named(), non_feature_columns(), L1 -- the columns that are the record, not the model's input.…, Render offenders for a message: sorted, truncated, and counted., The columns a featuriser must carry through, in the order they appear in the… (+10 more)

### Community 93 - "Target"
Cohesion: 0.14
Nodes (18): _apply(), _expm1(), _model_space_label(), Any, Series, ValueError, L1 -- the modelled target is ``log1p(wt%)``, and this is the only module that…, A value cannot be moved between the two target spaces, and the message says… (+10 more)

### Community 94 - "088 Group Aware Nested"
Cohesion: 0.11
Nodes (19): Card #80: API reference documentation, docs/API.md, Refusal versus a genuinely low prediction, Parity plot with the LOACO version at the same scale, Leak L8: splits grouped on the raw formula string, Card #88: Group-aware nested cross-validation protocol, A fold id is issued for content, not by counting, Leak L4: the same splits object tunes and then reports (+11 more)

### Community 95 - "Evaluate"
Cohesion: 0.14
Nodes (18): metrics_table(), R2, RMSE, MAE and the quantile metrics on both scales, each with two intervals.…, _out_of_fold(), DataFrame, AC-1's question, asked of this module. An interval that moves between runs is…, Not the mean of the replicates, and this is the one definition of it.…, R2 on log1p capacity and R2 in weight percent are different claims about the…, Card #29 settled this against prose, and gave the reason: prose is what a… (+10 more)

### Community 96 - "005 Gate Harness Prd"
Cohesion: 0.13
Nodes (18): Lu et al. — 27 unreported alloy compositions, Card #65 — OPTIMADE cross-check for prior art, OPTIMADE federated query (AFLOW, COD, Materials Cloud, Materials Project, NOMAD, odbx, OQMD), A network failure degrades to UNKNOWN, never to NOVEL, Card #4 — Artifact store and manifest contract, FeatureContract.as_manifest() embedded in the model manifest, Every payload carries a SHA-256; load re-hashes and raises PayloadCorrupt, For an artifact, SKIPPED is treated exactly as FAILED (+10 more)

### Community 97 - "Hydride Domain Grounding"
Cohesion: 0.13
Nodes (18): The band is wide relative to the physics, The material-versus-system caveat, The enabling fact survives the re-selection, Angelopoulos & Bates 2023 — Conformal Prediction: A Gentle Introduction, What composition-based features cannot encode, Conformal prediction for distribution-free intervals, A DFT enthalpy is not an experimental measurement, DOE onboard storage targets (TED, updated May 2017) (+10 more)

### Community 98 - "091 The Prediction Record"
Cohesion: 0.16
Nodes (18): The prediction assembly order, Card #85: ADR — the delivery seam, The library owns no I/O: predict_capacity() is pure, One cache or two: the delivery bundle and the memoised surrogate, Card #90: The refusal catalogue, Declared versus reachable reason codes, This repository catches bugs by refusing, not by logging, One sentence this page cannot show (+10 more)

### Community 99 - "Report"
Cohesion: 0.12
Nodes (18): Models Evaluated Table, bootstrap_ci(), optuna_stacking_objective(), weighted_score(), ExtraTrees Best Single Model, Stacking Ensemble (best overall), 13-Model Regression Benchmark, Bootstrap Confidence Intervals (2000 resamples) (+10 more)

### Community 100 - "Build Element Tables"
Cohesion: 0.22
Nodes (17): build_cbfv_reference(), build_cbfv_statistics(), build_jarvis(), build_oliynyk(), _cell(), _column_index(), main(), normalise() (+9 more)

### Community 101 - "Model"
Cohesion: 0.13
Nodes (10): FitLog, FitRecord, Which rows one fit saw in which role, and what the fit cost. The evidence the…, One row of :meth:`FitLog.table`., Every fit a run made, in order. Passed in rather than kept in module state, so…, One row per fit: where it was, how many rows in each role, what it cost., An ndarray carries no column names, so a permuted matrix would be plausible and…, It records identities and reports counts, which is what makes it writable to a… (+2 more)

### Community 102 - "081 App Chart Vocabulary"
Cohesion: 0.12
Nodes (17): Card #81: App chart vocabulary, Domain strip chart, Nearest neighbours chart (k closest by ElMD), A number rendered large and alone reads as certain, Prediction band chart, Temperature sweep chart, The app is an HTTP client of the service, not an in-process caller, app/main.py — the primary user journey (+9 more)

### Community 103 - "Manifest"
Cohesion: 0.16
Nodes (16): describe_git(), digest_file(), Path, Read the current commit and branch at ``root``, and whether its **code** is…, The SHA-256 and byte length of one file. What makes a stored payload checkable.…, Path, An installed package in a container has no work tree. Refusing to save an…, The defect this field was renamed for: a run dirties its own provenance stamp.… (+8 more)

### Community 104 - "Metadata"
Cohesion: 0.13
Nodes (16): class_distribution(), DataFrame, The frame with its canonical key attached and its ``Alloy_class`` reconciled.…, What reconciliation did to each class, in rows and in compositions. The…, with_metadata(), Counted in compositions, because #88's folds group on the canonical key. The…, The card asked for ``UNKNOWN``. The curated file needs none -- the class is…, Class by class, not as a total. Measured during card #12; a change here is a… (+8 more)

### Community 105 - "061 Element Subset Outer"
Cohesion: 0.16
Nodes (16): Card #61 — Element-subset outer loop, Fixed element subset per run, swept in an outer loop, hydms.search.sweep, Card #62 — Hypervolume convergence study, Hypervolume versus generation as convergence evidence, pymoo chosen over Optuna's sampler, Card #63 — Multi-seed stability study, Front is a property of the problem, not of the seed (+8 more)

### Community 106 - "076 Predict Capacity Over"
Cohesion: 0.14
Nodes (16): temperature_window() — the worked config-driven screen, an outer bound only, ArtifactBundle — a version plus the screens and their references, _check_columns — the bundle is the only place screens and _candidate can be made to agree, The forced ordering: null-check, featurise, predict, screen, resolve, answer, predict_capacity(formula, temperature_k) — the phase's deep module, reference_digests — digested, not pinned (fit-time binding owed by #91), resolve() — one composition rule for many screen verdicts, NOT_ALWAYS: NEVER is red if it appears, SOMETIMES is reported never required (+8 more)

### Community 107 - "035 Contextmd Domain Glossary"
Cohesion: 0.16
Nodes (15): hydms/gates/_artifact.py: the require_gates=False door for gates, surrogate_from(bundle): assembling split from locating, One definition of the deployed fit (hydms/surrogate/deploy.py), --report is also an input path (the CatBoost-defaults trap), CONTEXT.md — 26 terms in nine groups, Inclusion rule: a term is in only if conflating it already cost something, Sentinel subject — glossary term born of the L11 drift, Three R² values need three names: procedure, artifact, transfer (+7 more)

### Community 108 - "034 Train And Publish"
Cohesion: 0.14
Nodes (15): artifacts/v2 — the version to promote, Train and publish the deployed artifact version, A run re-reads pipeline.yaml mid-flight (~2,300 windows), The manifest records the run's own SHA, not promotion-time HEAD, python -m hydms.surrogate.promote, The waiver summary counts wrong and no test asserts the string, A waiver is an act, not a property, tests/artifacts/test_waiver_scope.py — waivable set derived from the boards (+7 more)

### Community 109 - "087 Canonical Composition Key"
Cohesion: 0.14
Nodes (15): ALLOY_CLASS_PRECEDENCE: reconcile by precedence, not by majority, canonical_key(): identity insensitive to order, scaling, whitespace and case, Card #87: Canonical composition key and Alloy_class reconciliation, The 1149 → 1142 → 1121 → 1115 collapse, Four significant digits: the resolution the key rounds to, group_keys(): the single grouping seam for splits and folds, The L13 sentinel: Alloy_class survives featurisation, separation(): nothing merged is farther apart than something not merged (+7 more)

### Community 110 - "Report"
Cohesion: 0.15
Nodes (15): Feature Category Correlation Analysis, Expanded Material Science Linkage Summary, Mutual Information vs Pearson Analysis, Temperature Subgroup Performance Table, 22 Selected Features, avg_is_alkaline, avg_polzbl_divi_atom_mass, avg_valence_d (+7 more)

### Community 111 - "Inverse Design Methods"
Cohesion: 0.15
Nodes (15): Unique-Formulae Split Basis (1149 of 1279), get_temp_group(), Model Limitations, Temperature Subgroup Performance, Applicability Domain and Novelty Control, Beltrame et al. 2025 - dataset size and augmentation in hydrides, Dan et al. 2020 - MatGAN, De Breuck et al. 2021 - MODNet (+7 more)

### Community 112 - "Inverse Design Methods"
Cohesion: 0.16
Nodes (15): Bayesian Optimisation / Active Learning, Cost, Criticality and Toxicity Screen, Deb et al. 2002 - NSGA-II, Enumerate-and-Screen (Architecture A), Ji et al. 2025 - ML-driven GA for BCC MPEAs, Liang et al. 2025 - Whale Optimization alloy design, Inverse Design Methods Memo, Constrained Multi-Objective EA (Architecture B) (+7 more)

### Community 113 - "Store"
Cohesion: 0.16
Nodes (6): Artifacts, Any, One loaded artifact version: the objects, and the manifest that vouches for…, The payload keys this version holds, in the order they were saved., The columns the stored model was fitted on, in fitting order., The stored :class:`~hydms.descriptors.contract.FeatureContract`, digest checked.

### Community 114 - "Select"
Cohesion: 0.23
Nodes (12): _emit(), main(), _parser(), ArgumentParser, DataFrame, Namespace, Path, TextIO (+4 more)

### Community 115 - "006 Ci Fast Lane"
Cohesion: 0.18
Nodes (13): Card #6 — CI fast lane: lint, tests and gates, The conda-free hygiene job — lint and types build no environment, math.log1p differs by one ulp between MSVC and glibc, environment.lock.yml is win-64 by construction and cannot restore on Linux, A lint lane on a version floor is not a check — ruff pinned exactly, The old push:branches:[main] trigger meant the Phase H branch was never checked, train.py --budget over-projects by ~45 % (scored fits only, no pruning model), Card #7 — CI slow lane: retrain, upload and version promotion (+5 more)

### Community 116 - "086 Gate Hg 4"
Cohesion: 0.17
Nodes (13): Card #86: GATE HG-4 — CI fast lane with delivery suite and hygiene, The conda-free hygiene job (ruff and mypy), The coverage floor is currently unenforceable, Whether openpyxl is added, or the HyStor spreadsheet stays unread, Fifty-five elements, not fifty-four, What a new card must carry, scripts/check_board.py — the board integrity check, The hardening board — Phase H (+5 more)

### Community 117 - "Inverse Design Methods"
Cohesion: 0.15
Nodes (13): Analysis Notebook Suite, Non-Standard Formula Inventory, Raw Data Summary (1279 x 6), Shapiro-Wilk Normality Test on H2 wt%, Matminer Miedema and WenAlloys Features, Ward et al. 2018 - Matminer, Non-Standard Composition Formats, Raw Outlier Analysis (+5 more)

### Community 118 - "Tooling"
Cohesion: 0.15
Nodes (10): pytest_config(), Regression tests for the test tooling itself. These exist because two of the…, Gate HG-1's sentinels are selected by marker; an unregistered marker errors…, Setting `norecursedirs` replaces pytest's defaults rather than extending them.…, If these were ever made safe, the interlock could be relaxed. Until then, it…, No collected module may live outside tests/ — the interlock's observable…, test_collected_tests_come_only_from_this_directory(), test_leak_marker_is_registered() (+2 more)

### Community 119 - "Check Database"
Cohesion: 0.17
Nodes (6): Item, pytest, sqlite3, pytest_collection_modifyitems(), The HG-1 sentinel suite: one test per named leak. Every test under this…, Mark everything collected from this directory as a leak sentinel.

### Community 120 - "001 Pin And Lock"
Cohesion: 0.17
Nodes (12): Rebuild blocked by HTTP 403 on the defaults channel, conda env export writes python-graphviz into the pip block, Card #1 — Pin and lock the Project conda environment, One lock file had to become two (conda + pip --no-deps), CBFV is unlicensed and must never become a runtime dependency, GPL-3.0-or-later replaces the MIT licence, Core deps exclude what is not yet installed; uq/search/novelty/app/parity extras, Card #2 — Scaffold the hydms package with pyproject and GPL-3.0 (+4 more)

### Community 121 - "030 Leave One Alloy"
Cohesion: 0.17
Nodes (12): Leak L6: features chosen on rows the folds then score, Leaks L1 and L5: early stopping on the test set, Angelopoulos & Bates 2023 — distribution-free conformal prediction, Card 27: MAPIE conformal calibration, Card 28: predict() — the surrogate's public interface, Card 29: Evaluation metrics with bootstrap confidence intervals, Leak L11: SHAP and PDP computed on X_test, Beltrame et al. 2025 — hydride models transfer poorly across families (+4 more)

### Community 122 - "033 Gate Ac 4"
Cohesion: 0.17
Nodes (12): Compare like with like: calibrated_heads, not raw heads, GATE AC-4: known alloys round-trip through predict(), Failure output separates column ORDER from a different computation, _spread(): deterministic round-robin over Alloy_class, Column-order independence: _batch selects the fitted names, answer_from() — the one door back from JSON, The delivery contract: request, result and refusal schemas, hydms/delivery/contract.py — PredictionResult, Refusal, Interval, verdicts (+4 more)

### Community 123 - "Report"
Cohesion: 0.17
Nodes (12): Capacity Prediction from Formula and Temperature, HyStor Experimental Database, ML-HYDPARK v0.0.5 Dataset, Kauwe et al. - CBFV, Future Directions, HydMS Project Report, Wilson et al. 2024 - HyStor Database, Choudhary et al. 2020 - JARVIS (+4 more)

### Community 124 - "Spike Feature Provenance"
Cohesion: 0.24
Nodes (11): build_sample(), columns_for(), load_selected(), main(), DataFrame, Resolve which CBFV element-property table produces each selected feature. Card…, The feature names the published pipeline selected, in SHAP-importance order., Column names CBFV emits for one table, using the original script's exact… (+3 more)

### Community 125 - "Waiver Scope"
Cohesion: 0.21
Nodes (11): board_of(), owners(), Which criteria a Phase H promotion may waive, derived from the board rather…, Which board directory holds this card, by the id its filename carries., Every registered criterion and the card that owes it., A criterion whose card cannot be found is one whose scope cannot be decided at…, The derivation, and the pin. If this fails after a card moved between boards,…, Everything not waivable is work, and work has a card on the board being worked.… (+3 more)

### Community 126 - "Scaler"
Cohesion: 0.27
Nodes (7): Any, NoReturn, Always raises. A fitted scaler is a value, and refitting it is the leak., Always raises -- the scikit-learn shortcut, and the one that hides a refit., Always raises. Updating the statistics from candidates is the same defect., ``RobustScaler`` with the percentiles pinned, imported lazily. Deferred so that…, _robust_scaler()

### Community 127 - "Selection"
Cohesion: 0.20
Nodes (6): FoldSelection, One selection per outer fold, and what the folds agree about. There is…, Features every fold selected, in the first fold's order. The conservative…, Every feature any fold selected, in first-seen order. The permissive reading., Fold by fold: rows fitted on, rows removed, features selected, and which. The…, How many folds selected each feature, most agreed-upon first. The number that…

### Community 128 - "023 Scaler Fit Once"
Cohesion: 0.18
Nodes (11): FittedScaler — a transform-only wrapper with no fit, The persisted scaler has lost its named consumer (open), Persist the result, not the estimator, MultiQuantile:alpha=0.1,0.5,0.9 — the interval-emitting head, The artifact stores the correction as a number, not a pickled MAPIE object, Raw quantile heads cover 64.4% against a nominal 80%, lcb is a first-class output so no caller can rank on the mean, The model consumes raw, unscaled features (+3 more)

### Community 129 - "044 Screen Interface A"
Cohesion: 0.22
Nodes (11): apply_screens — the protocol is a promise, the runner is the enforcement, Screen a batch, never a candidate at a time (5 ms featurize floor), Screen interface: a verdict with a reason, never a silent drop, _fingerprint: position-weighted content hash catches in-place mutation, INDETERMINATE: a screen that cannot judge rejects (fail-closed), Screen protocol (name, verdict(), declared reason vocabulary), Element Mover's Distance novelty screen, ElMD mod_petti has a closed form: cdist(cumsum) cityblock (+3 more)

### Community 130 - "Check Freeze"
Cohesion: 0.35
Nodes (10): changed_paths(), check(), exempt(), freeze_in_force(), _git(), main(), Path, Enforce the Phase H implementation freeze against a pull request's diff. The… (+2 more)

### Community 131 - "Predict"
Cohesion: 0.20
Nodes (9): AssertionError, _alloys(), fitted(), _frame(), DataFrame, Forty distinct AB5-family compositions, all near the corpus ElMD knows. The…, The fixture corpus, featurised for real -- the path from a formula string…, One fitted model and its calibration, over the fixture corpus. (+1 more)

### Community 132 - "Validation"
Cohesion: 0.20
Nodes (6): FoldSpace, The numbering that makes two folds *the same fold* when they hold out the same…, The id of the fold holding out exactly these keys, issuing one if it is new., The id already issued for these keys, or ``None``. Never issues one. The read-…, test_an_unseen_fold_has_no_id_and_asking_does_not_issue_one(), test_two_folds_over_the_same_materials_share_an_id()

### Community 133 - "009 Raw Loaders With"
Cohesion: 0.22
Nodes (10): Open: whether a declared correction layer sits above the loader, The dataset uses 55 elements, not the 54 REPORT.md states, The HyStor spreadsheet has no loader (openpyxl absent, not a fourth source), The loader normalises nothing — whitespace and malformed formulae pass through, Schema bounds ask 'is this a temperature at all?', not 'is it in range?', Card #9 — Raw loaders with schema validation, log1p / expm1 as the only two transform entry points, A named Series carries its space; log_log_ cannot be produced (+2 more)

### Community 134 - "Evaluate"
Cohesion: 0.22
Nodes (9): Any, ``resamples`` arrays of positional row indices, drawn with replacement. **The…, _replicates(), 83 of the 780 real training groups span more than one temperature. So a group…, Q6: one resample, every breakdown computed from it — and it is shared by…, The property, at its sharpest: one material, and the group bootstrap has no…, test_a_group_resample_draws_whole_compositions_and_a_row_resample_does_not(), test_a_resampled_group_carries_all_of_its_rows() (+1 more)

### Community 135 - "Selection"
Cohesion: 0.22
Nodes (5): The chosen features, and every count behind them. Attributes: features: The…, How many features were selected., The counts and the chosen names as one row of a table of selections. Defined…, Stage by stage: in, out, dropped, restored -- the counts the card asks be…, Selection

### Community 136 - "012 Re Join Alloy"
Cohesion: 0.28
Nodes (9): Missing keys raise as loudly as unknown ones, Alloy_class validated against a closed set of ten, The unwired sentinel turns HG-1 red before a wrong line is written, AC-6 feasible counted in compositions: smallest class A2B with 24 of 1115, L13 sentinel — assert_metadata_survives over the real featurisation path, Leak L8 — joining on the raw formula string re-imports the collision, A row with a missing class refuses; there is no UNKNOWN, Card #12 — Re-join Alloy_class on the canonical key (+1 more)

### Community 137 - "Composites"
Cohesion: 0.22
Nodes (9): _fixture_rows(), _pack(), ndarray, parametrize, Formulae to the ``(n_compositions, max_arity)`` pair :func:`statistics` takes., One pin per feature, computed with a pencil rather than with the code under…, Statistic-of-composite reproduces CBFV; composite-of-statistic misses it by 2%…, test_each_selected_jarvis_feature_matches_a_hand_computed_value() (+1 more)

### Community 138 - "Canonical"
Cohesion: 0.25
Nodes (5): Collapse, CollapseStage, One normalisation step and what it merged. Attributes: name: ``"raw"``,…, The accounting of 1149 formula strings down to 1115 compositions. Reported per…, Account for the collapse from formula strings to compositions, step by step. On…

### Community 139 - "008 Provenance Spike Resolve"
Cohesion: 0.25
Nodes (8): extract_features_cbfv.py:31 passes elem_prop='magpie' and reproduces nothing, Statistic-of-composite versus composite-of-statistic (risk R3), unresolved, The 22 features split 15 oliynyk / 6 jarvis / 1 temperature passthrough, Card #8 — PROVENANCE SPIKE: resolve elem_prop for all 22 features, Run the real featuriser rather than diffing table headers, CBFV.composition.parse_formula validates nothing, The Gordy hole — the 22-feature contract refuses 266 of 1279 curated rows, Two hard gates: #8 provenance spike and #21 featuriser parity

### Community 140 - "010 Keyed Merge Replacing"
Cohesion: 0.29
Nodes (8): (Composition, temperature(K)) is not unique: 1279 rows, 1272 pairs, merge_datasets.py:49 keeps the first of two identically-named columns, Card #10 — Keyed merge replacing the positional concat, Leak L9 — positional pd.concat(axis=1) with no join key, hydms.data.merge.merge_features, The spine's index label is the row identity, Compute the log target, never join it from hydride_prefeaturizing.csv, temperature(K) arrives twice in the concat — a third disguise of merge_datasets.py:49

### Community 141 - "073 End To End"
Cohesion: 0.25
Nodes (8): Leak L9: positional concat at merge_datasets.py:46 invalidates the Miedema result, The card's L9 wording conflates two properties of a keyed merge, SMOKE_SPLIT and SMOKE_FOREST_TREES — budgets that change how, not which, End-to-end smoke pipeline on a sampled fixture, The fixture is filtered to what the feature contract can serve, smoke-fixture.csv — generated by --emit, shape-checked by check_fixture(), The smoke runs the live stage order, not the archival one, python -m hydms.pipeline.smoke — the whole chain in 12.1 s

### Community 142 - "Metadata"
Cohesion: 0.25
Nodes (8): curated(), matrix(), DataFrame, Three rows shaped like `with_metadata`'s output, on a non-trivial index. The…, What a featuriser returns: float64 features on the caller's own labels., The curated dataset, loaded once. Read-only: nothing here mutates it., record(), resolved()

### Community 143 - "Readme"
Cohesion: 0.29
Nodes (7): Twelve layer subpackages derived from the cards, HydMS Inverse Design Board (frozen), Tickets cut by layer, not by phase, The eight layers L0–L7, The evaluator is the deep module; Search is a seam, The five phases P0, P1, PT, PA, PB, Phase 1 has two halves: code (9–34) and prose (37)

### Community 144 - "069 Infrastructure Pytest Ruff"
Cohesion: 0.29
Nodes (7): .github/workflows/integrity.yml, Test infrastructure: pytest, ruff, mypy and the coverage floor, Coverage floor fail_under = 80 on hydms/, Legacy Machine_Model tests excluded by configuration, not by rename, norecursedirs replaces pytest's defaults, it does not extend them, scripts/check_freeze.py — the diff half, with the migration exemption, docs/FREEZE.md — the freeze, the denied paths, the unfreeze condition

### Community 145 - "Inverse Design Methods"
Cohesion: 0.33
Nodes (6): Baird et al. 2022 - DiSCoVeR, Conditional Generative Design (Architecture C), Element Mover's Distance (ElMD), Lu et al. 2025 - FIND platform, Do-Not-Rediscover-Known-Alloys Check, OPTIMADE Federated Query API

### Community 146 - "Element Data"
Cohesion: 0.40
Nodes (3): ndarray, One number, or an exception that says exactly what is missing. Never returns…, ``prop`` for each element, in the order given. The array is what the…

### Community 147 - "Loco"
Cohesion: 0.40
Nodes (5): _estimable(), per_class(), Series, One row per alloy class: what it scored, over how much, and whether that means…, Whether a class fold's R2 is a number at all, and if not, why not in words.…

### Community 148 - "Scaler"
Cohesion: 0.40
Nodes (3): DataFrame, Scale a batch, by name, in fitting order. The columns must be exactly…, One row per feature: its centre, its scale, and whether its span was zero. For…

### Community 150 - "Hg2 Refusal Path"
Cohesion: 0.50
Nodes (4): _exits(), How many exits ``predict_capacity`` has, and every finding about them. A probe…, The card's "asserted exhaustively, not sampled": the count is of returns, not…, test_it_reports_how_many_exits_it_read_rather_than_how_many_it_sampled()

### Community 151 - "Comparison"
Cohesion: 0.50
Nodes (3): Placeholder, How far a placeholder in an element table reaches into the curated rows.…, The exposed share of the curated rows, as a fraction.

### Community 152 - "030 Leave One Alloy"
Cohesion: 0.50
Nodes (4): Estimability is a property of R2, not a taste, AC-6's gate reads the committed tables rather than refitting, The LOCO run: ten class folds, 4 h 07 m, committed tables, Untracked probe tables cited by value in three committed documents

### Community 153 - "Scaler"
Cohesion: 0.33
Nodes (4): The real feature matrix and its split assignment, built the way the pipeline…, Six training rows, one validation row, one test row -- on the matrix's own…, real_training_matrix(), split()

### Community 154 - "015 Data Layer Golden"
Cohesion: 0.67
Nodes (3): The 1,115-vs-1,114 off-by-one is Eu1Ni5, Eu1Ni5 (row 516) — a corrupted published feature row, No europium-containing formula may be compared at all

### Community 155 - "022 Featurisation Throughput Benchmark"
Cohesion: 0.67
Nodes (3): Throughput 242 / 14,291 / 40,848 / 44,831 formulae per second, Risk R6: NSGA-II's surrogate-call budget vs enumeration, PropertyTable.servable — the 13x regression a repeated fixture hid

### Community 156 - "Canonical"
Cohesion: 0.67
Nodes (3): MonkeyPatch, `docs/QA-PROTOCOL.md` section 5: the measurement is shown red on purpose. At…, test_three_significant_digits_would_merge_two_materials()

### Community 157 - "Target"
Cohesion: 0.67
Nodes (3): published(), Series, The raw target and the published log column, in file order. Positional…

## Ambiguous Edges - Review These
- `Models Evaluated Table` → `13-Model Regression Benchmark`  [AMBIGUOUS]
  Machine_Model/README.md · relation: references

## Knowledge Gaps
- **136 isolated node(s):** `Akiba et al. 2019 - Optuna`, `Angelopoulos & Bates 2023 - Conformal Prediction`, `Baird et al. 2022 - DiSCoVeR`, `Choudhary et al. 2020 - JARVIS`, `Dan et al. 2020 - MatGAN` (+131 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Models Evaluated Table` and `13-Model Regression Benchmark`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `load()` connect `Config` to `Prediction Request Path`, `Delivery Refusal Vocabulary`, `Leak Sentinels`, `Canonical Composition Key`, `Evaluate`, `Element Mover's Distance Novelty`, `Surrogate Prediction Interface`, `Feature Selection Inside Folds`, `Smoke Pipeline Fixture`, `Quantile Model Fitting`, `Leak Inventory`, `Raw Data Loaders`, `Gate Harness Registry`, `Conformal Calibration`, `Loco`, `Surrogate Training Run`, `Calibrated Quantile Heads`, `Applicability Domain Screen`, `Artifact Store Promotion`, `Grouped Data Splits`, `Gate CLI Reporting`, `Comparison`, `Comparison`, `Load`, `Benchmark`, `Loco`, `Ac2 Parity`, `Validation`, `Model`, `Evaluate`, `Window`, `Promote`, `Clean`, `Hg2 Refusal Path`, `Selection`, `Validation`, `Metadata`, `Deploy`, `Protocol`, `Novelty`, `Store`, `Domain`, `Store`, `Target`, `Ac6 Loco`, `Screening`, `Evaluate`, `Loco`, `L13 Class Survival`, `Init`, `Ac1 Reproducibility`, `Artifact`, `Metadata`, `Evaluate`, `Metadata`, `Select`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Why does `featurize()` connect `Featuriser Element Tables` to `Prediction Request Path`, `Delivery Refusal Vocabulary`, `Leak Sentinels`, `Predict`, `Descriptor Feature Contract`, `Surrogate Prediction Interface`, `Feature Selection Inside Folds`, `Smoke Pipeline Fixture`, `Quantile Model Fitting`, `Descriptor Computability`, `Surrogate Training Run`, `Scaler`, `022 Featurisation Throughput Benchmark`, `Acceptance Criteria Gates`, `Load`, `Benchmark`, `Metamorphic`, `Ac4 Round Trip`, `L13 Class Survival`, `016 Element Property Tables`, `Golden`, `Scaler`, `Metadata`, `Select`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `FeatureContract` connect `Descriptor Computability` to `Featuriser Element Tables`, `Prediction Request Path`, `Delivery Refusal Vocabulary`, `Leak Sentinels`, `Descriptor Feature Contract`, `Surrogate Prediction Interface`, `Feature Selection Inside Folds`, `Smoke Pipeline Fixture`, `Quantile Model Fitting`, `Artifact Manifest`, `Acceptance Criteria Gates`, `Comparison`, `Comparison`, `Benchmark`, `Metamorphic`, `L13 Class Survival`, `016 Element Property Tables`, `Golden`, `014 Cleanlab Screening As`, `Artifact`, `Scaler`, `Select`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `featurize()` (e.g. with `PropertyTable` and `Statistics`) actually correct?**
  _`featurize()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 49 inferred relationships involving `ScreenError` (e.g. with `ApplicabilityDomain` and `DomainReference`) actually correct?**
  _`ScreenError` has 49 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Akiba et al. 2019 - Optuna`, `Angelopoulos & Bates 2023 - Conformal Prediction`, `Baird et al. 2022 - DiSCoVeR` to the rest of the system?**
  _136 weakly-connected nodes found - possible documentation gaps or missing edges._