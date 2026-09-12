# Graph Report - Hydride_Machine_learning_project  (2026-09-12)

## Corpus Check
- 23 files · ~497,588 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5369 nodes · 12308 edges · 229 communities (203 shown, 26 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 872 edges (avg confidence: 0.6)
- Token cost: 357,741 input · 0 output

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
- Target
- Composites
- Applicability
- Benchmark
- Harness
- Stats
- 059 Pymoo Problem Definition
- Contract
- L3 L10 Holdout Immutability
- Window
- Model
- L11 Explainability
- Protocol
- Config
- Promote
- Metadata
- Validation
- Comparison
- Store
- Validation
- Deploy
- Cleanlab
- Novelty
- L1 L5 Early Stopping
- L2 L4 Model Selection
- Domain
- Selection
- 014 Cleanlab Screening As
- Ac4 Round Trip
- Comparison
- Merge
- L12 Sample Weights
- Novelty
- L7 L8 Grouping
- Validation
- Conftest
- L9 Keyed Merge
- Predict
- Golden
- L13 Class Survival
- Evaluate
- Evaluate
- Ac2 Parity
- Phase H Runbook
- Inverse Design Methods
- 016 Element Property Tables
- L6 Selection Independence
- Scaler
- Scaler
- Report
- Requirements Lock
- Report
- Metadata
- Loco
- No Leak
- Init
- Ac1 Reproducibility
- Inverse Design Methods
- Phase H Runbook
- Old Vs New
- Contract
- Cli
- Novelty
- 090 The Refusal Catalogue
- Prd Inverse Design
- Sources
- Canonical
- Scaler
- Hydride Domain Grounding
- Novelty
- Hg2 Refusal Path
- Context
- Refusals
- 077 Gate Hg 2
- Phase H Runbook
- Hg2 Refusal Path
- Comparison
- 048 Applicability Domain Ceiling
- Hg2 Refusal Path
- Readme
- Validation
- 005 Gate Harness Prd
- Domain
- Loco
- Loco
- Model
- Scaler
- Evaluate
- Manifest
- Evaluate
- Evaluate
- Predict
- Readme
- Report
- 061 Element Subset Outer
- 034 Train And Publish
- Phase H Runbook
- Store
- 033 Gate Ac 4
- 069 Infrastructure Pytest Ruff
- 087 Canonical Composition Key
- Running The Fit
- Store
- Loco
- Predict
- 006 Ci Fast Lane
- 073 End To End
- 044 Screen Interface A
- Tooling
- Requirements
- Readme
- Comparison
- Comparison
- 001 Pin And Lock
- 081 App Chart Vocabulary
- Spike Feature Provenance
- Contract
- Scaler
- Selection
- 023 Scaler Fit Once
- 071 Gate Hg 1
- 074 Metamorphic For Featurize
- Context
- Benchmarks
- Hg2 Refusal Path
- Validation
- 009 Raw Loaders With
- 088 Group Aware Nested
- Predict
- Screening
- Evaluate
- Selection
- 012 Re Join Alloy
- 010 Keyed Merge Replacing
- Context
- Canonical
- Metadata
- Refusals
- 008 Provenance Spike Resolve
- Metadata
- Protocol
- Prd Inverse Design
- Novelty
- Readme
- 076 Predict Capacity Over
- Inverse Design Methods
- Report
- Novelty
- Qa Protocol
- Canonical
- Artifact
- Loco
- Check Database
- Canonical
- Predict
- Scaler
- Ci
- Hg2 Refusal Path
- Scaler
- 084 Batch Csv Screening
- Context
- Refusals
- Ac3 Conformal Coverage
- Ac4 Known Alloy Round
- Comparison
- 030 Leave One Alloy
- Verify Environment
- Hg2 Refusal Path
- Context
- Context
- Ac3 Conformal Coverage
- Ac6 Leave One Class
- Core
- Predict
- 015 Data Layer Golden
- 029 Evaluation Metrics With
- Report
- Canonical
- Loco
- Context
- Environment
- Phase H Runbook
- Prd Inverse Design
- Init
- Init
- Init
- Init
- Init
- Init
- Init
- Canonical
- Comparison
- Comparison
- Scaler
- Validation
- Freeze
- Misc Fragments
- Misc Fragments
- Misc Fragments
- 024 Port Feature Selection
- Pyproject

## God Nodes (most connected - your core abstractions)
1. `load()` - 181 edges
2. `Config` - 132 edges
3. `_fixture()` - 103 edges
4. `featurize()` - 97 edges
5. `ScreenError` - 85 edges
6. `parse_formula()` - 80 edges
7. `ContractError` - 71 edges
8. `ModelSettings` - 69 edges
9. `FeatureContract` - 67 edges
10. `load_hydride_data()` - 62 edges

## Surprising Connections (you probably didn't know these)
- `FeatureContract` --implements--> `Computability is recorded per composition, not per feature`  [EXTRACTED]
  hydms/descriptors/contract.py → kanban-hardening/019-the-22-feature-contract.md
- `Leak L6: features chosen on rows the folds then score` --rationale_for--> `select_across_folds()`  [EXTRACTED]
  kanban-hardening/024-port-feature-selection-inside-the-folds-reading-cleanlab.md → hydms/surrogate/selection.py
- `One parser, not three — pymatgen is available and still declined` --rationale_for--> `parse_formula()`  [EXTRACTED]
  kanban-hardening/020-featurize-the-descriptor-layers-public-interface.md → hydms/data/load.py
- `A group-disjoint calibration carve from train, never from val or test` --references--> `group_keys()`  [INFERRED]
  kanban-hardening/027-mapie-conformal-calibration.md → hydms/data/canonical.py
- `Card 19: The 22-feature contract` --references--> `assert_contract()`  [EXTRACTED]
  kanban-hardening/019-the-22-feature-contract.md → hydms/descriptors/contract.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **The Refusal Path: Never a Bare Number** — kanban_hardening_077_gate_hg_2_the_refusal_path_never_a_bare_number_gate_hg_2, kanban_hardening_077_gate_hg_2_the_refusal_path_never_a_bare_number_predict_capacity, kanban_hardening_077_gate_hg_2_the_refusal_path_never_a_bare_number_prediction_result, kanban_hardening_077_gate_hg_2_the_refusal_path_never_a_bare_number_refusal, docs_refusals_refusal_catalogue, context_prediction [EXTRACTED 1.00]
- **The Three Score Readings and Their Qualifier** — context_procedure_score, context_artifact_score, context_transfer_score, context_as_published, context_probe [EXTRACTED 1.00]
- **Why Inverse Design Is Viable Here (forward featurisation chain)** — docs_prd_inverse_design_enabling_fact, graphify_out_memory_query_20260829_164821_why_does_inverse_design_methods_memo_bridge_the_in_descriptor_non_invertibility, research_inverse_design_methods_optimize_in_composition_space, readme_extract_features_cbfv, report_22_selected_features, docs_prd_inverse_design_featuriser_reimplementation [INFERRED 0.95]
- **Grouping by canonical composition closes L7 and L8** — docs_phase_h_runbook_l7, docs_phase_h_runbook_l8, docs_phase_h_runbook_hydms_data_canonical, docs_phase_h_runbook_hydms_data_splits, docs_phase_h_runbook_hydms_surrogate_validation, docs_phase_h_runbook_assert_disjoint_groups [EXTRACTED 1.00]
- **The deployed fit: screen, carve, fit, calibrate — one definition** — docs_phase_h_runbook_hydms_surrogate_deploy, docs_phase_h_runbook_hydms_data_screening, docs_phase_h_runbook_hydms_surrogate_model, docs_phase_h_runbook_hydms_surrogate_conformal, docs_running_the_fit_step5_calibrate, hydms_config_pipeline_calibration_folds [EXTRACTED 1.00]
- **Two-table featurisation and what AC-2 parity can mean** — hydms_descriptors_feature_provenance_mapping, hydms_descriptors_data_sources_oliynyk_csv, hydms_descriptors_data_sources_jarvis_csv, hydms_descriptors_data_sources_cbfv_oliynyk_reference, docs_phase_h_runbook_ac_2, docs_phase_h_runbook_hydms_descriptors_featurize [EXTRACTED 1.00]
- **Architecture A screen-and-rank pipeline (propose, evaluate, rank, write, gate)** — kanban_052_the_proposer_seam_proposer, kanban_053_enumerate_proposer_stoichiometry_grid_over_the_simplex_enumerate, kanban_051_the_evaluator_candidates_in_full_evaluation_table_out_evaluate, kanban_054_lower_confidence_bound_ranking_lcb_ranking, kanban_055_screening_cli_entry_point_search_run, kanban_057_ranked_candidate_output_schema_and_writer_ac_7, kanban_056_gate_ac_8_guard_rail_strength_on_the_top_20_ac_8 [EXTRACTED 1.00]
- **Physical Interpretation Descriptor Set** — report_avg_valence_d, report_avg_is_alkaline, report_avg_polzbl_divi_atom_mass, report_dev_zunger_radii_sum, report_temperature_k [EXTRACTED 1.00]
- **The five-chart vocabulary that resists false belief** — kanban_hardening_081_app_chart_vocabulary_charts_that_resist_false_belief_prediction_band, kanban_hardening_081_app_chart_vocabulary_charts_that_resist_false_belief_domain_strip, kanban_hardening_081_app_chart_vocabulary_charts_that_resist_false_belief_temperature_sweep, kanban_hardening_081_app_chart_vocabulary_charts_that_resist_false_belief_nearest_neighbours_chart, kanban_hardening_081_app_chart_vocabulary_charts_that_resist_false_belief_parity_plot [EXTRACTED 1.00]
- **Generated documents rebuilt by --emit and pinned by a byte-identity test** — kanban_hardening_090_the_refusal_catalogue_docs_refusals_md, reports_loco_loco_report, reports_model_evaluation_report, reports_feature_selection_old_vs_new_report [EXTRACTED 1.00]
- **HydMS Ordered Pipeline Stages** — machine_model_src_merge_datasets, machine_model_src_log_transform_target, machine_model_src_extract_features_cbfv, machine_model_src_cleanlab, machine_model_src_boruta_feateng, machine_model_src_feature_selection, machine_model_src_split_data, machine_model_src_benchmark_model_selection, machine_model_src_catboostmodel [EXTRACTED 1.00]
- **Inverse-Design Guard Rail Stack** — research_inverse_design_methods_uncertainty_quantification, research_inverse_design_methods_applicability_domain, research_inverse_design_methods_physics_filters, research_inverse_design_methods_novelty_check, research_inverse_design_methods_lower_confidence_bound_ranking, research_inverse_design_methods_enumerate_and_screen [EXTRACTED 1.00]
- **L0 Foundation: environment, package, config, artifact store, gates, CI** — kanban_hardening_001_pin_and_lock_the_project_conda_environment_pin_project_env, kanban_hardening_002_scaffold_the_hydms_package_with_pyproject_and_gpl_30_licence_scaffold_hydms, kanban_hardening_003_config_loader_relative_paths_seeds_and_thresholds_in_one_pla_config_loader, kanban_hardening_004_artifact_store_and_manifest_contract_artifact_store, kanban_hardening_005_gate_harness_prd_acceptance_criteria_as_runnable_checks_gate_harness, kanban_hardening_006_ci_fast_lane_lint_tests_and_gates_on_cached_artifacts_ci_fast_lane, kanban_hardening_007_ci_slow_lane_full_retrain_artifact_upload_and_version_promot_ci_slow_lane [EXTRACTED 1.00]
- **Phase B evidence chain: subsets swept, converged, seed-stable, explored and figured** — kanban_061_element_subset_outer_loop_element_subset_outer_loop, kanban_062_hypervolume_convergence_study_hypervolume_convergence_study, kanban_063_multi_seed_stability_study_multi_seed_stability_study, kanban_066_streamlit_pareto_front_explorer_pareto_front_explorer, kanban_067_thesis_figure_set_thesis_figure_set [EXTRACTED 1.00]
- **The Phase H gate registry that promotion demands** — kanban_hardening_033_gate_ac_4_known_alloys_round_trip_through_predict_card, kanban_hardening_071_gate_hg_1_leak_sentinels_one_test_per_named_leak_card, kanban_hardening_077_gate_hg_2_the_refusal_path_never_a_bare_number_card, kanban_hardening_079_gate_hg_3_api_contract_tests_and_transport_parity_card, kanban_hardening_034_train_and_publish_the_deployed_artifact_version_promote [EXTRACTED 1.00]
- **Phase T thermodynamics chain (load, parameterise, train, sanity-check, apply, benchmark)** — kanban_038_ml_hydpark_thermodynamic_loader_card, kanban_039_parameterise_surrogate_training_by_target_card, kanban_040_train_the_enthalpy_and_entropy_surrogates_card, kanban_041_gate_ac_5_predicted_entropy_clusters_near_130_j_mol_h2_k_card, kanban_042_van_t_hoff_module_card, kanban_043_benchmark_against_witman_et_als_published_results_card [EXTRACTED 1.00]
- **Screen suite composed by the evaluator** — kanban_045_family_stoichiometry_screen_ab2_ab5_family_stoichiometry, kanban_046_valence_electron_concentration_window_screen_vec_window, kanban_047_atomic_size_mismatch_screens_size_mismatch_criteria, kanban_050_cost_and_supply_risk_screen_hhi, kanban_051_the_evaluator_candidates_in_full_evaluation_table_out_evaluate [EXTRACTED 1.00]
- **The descriptor layer's featurisation path: parse, table lookup, statistic, composite, contract** — hydms_data_load_parse_formula, hydms_descriptors_element_data_require_coverage, hydms_descriptors_stats_statistics, hydms_descriptors_composites_decompose, hydms_descriptors_contract_assert_contract, hydms_descriptors_featurize_featurize [EXTRACTED 1.00]
- **The delivery seam: one prediction path, one set of guard rails** — kanban_hardening_082_streamlit_forward_prediction_page_app_is_an_http_client, kanban_hardening_085_adr_the_delivery_seam_and_why_the_api_owns_no_ml_logic_library_owns_no_io, kanban_hardening_091_the_prediction_record_and_replay_prediction_record, kanban_hardening_091_the_prediction_record_and_replay_replay, kanban_hardening_085_adr_the_delivery_seam_and_why_the_api_owns_no_ml_logic_assembly_order [INFERRED 0.85]
- **The Phase H leak inventory addressed by these cards (L3, L6, L8, L10, L11, L12, L1/L5)** — kanban_hardening_013_stratified_unique_formula_splits_seeded_and_reproducible_leak_l8, kanban_hardening_014_cleanlab_screening_as_a_data_layer_stage_leak_l3, kanban_hardening_014_cleanlab_screening_as_a_data_layer_stage_leak_l10, kanban_hardening_014_cleanlab_screening_as_a_data_layer_stage_leak_l12, kanban_hardening_024_port_feature_selection_inside_the_folds_reading_cleanlab_leak_l6, kanban_hardening_026_catboost_multiquantile_with_honest_early_stopping_leaks_l1_l5, kanban_hardening_029_evaluation_metrics_with_bootstrap_confidence_intervals_leak_l11 [INFERRED 0.85]
- **The silent-misalignment defect family found across the data layer** — kanban_hardening_010_keyed_merge_replacing_the_positional_concat_leak_l9, kanban_hardening_010_keyed_merge_replacing_the_positional_concat_duplicated_column_silently_dropped, kanban_hardening_011_target_transform_module_compute_never_join, kanban_hardening_012_re_join_alloy_class_on_formula_temperature_duplicated_in_concat, kanban_hardening_012_re_join_alloy_class_on_formula_leak_l8_canonical_key [INFERRED 0.85]
- **Store the fitted result as a number, never a pickled estimator** — kanban_hardening_023_scaler_fit_once_persist_never_refit_result_not_estimator, kanban_hardening_023_scaler_fit_once_persist_never_refit_fittedscaler, kanban_hardening_027_mapie_conformal_calibration_correction_constant, kanban_hardening_019_the_22_feature_contract_order_is_a_declaration [INFERRED 0.85]
- **The --emit pattern: a generated file whose committed bytes a test asserts** — kanban_hardening_048_applicability_domain_ceiling_domain_reference, kanban_hardening_049_element_movers_distance_novelty_screen_novelty_reference, kanban_hardening_073_end_to_end_smoke_pipeline_on_a_sampled_fixture_fixture [INFERRED 0.95]

## Communities (229 total, 26 thin omitted)

### Community 0 - "Featuriser Element Tables"
Cohesion: 0.03
Nodes (107): PredictionResult, An answer with a number in it -- and therefore with an interval and a verdict.…, Always ``False``. A property, not a field, so it cannot be set to the wrong…, L6 — the boundary users meet: one prediction path, and the vocabulary it…, ArtifactBundle, bundle_from(), _candidate(), _check_columns() (+99 more)

### Community 1 - "Prediction Request Path"
Cohesion: 0.03
Nodes (108): PropertyTable, One element-property table, read once and never mutated. Frozen because a table…, A table from an in-memory ``{element: {property: value}}`` mapping. The…, Whether a real number can be produced, with no exception and no judgement., property -> the elements carrying it, built once on first use. Derived, so…, Every element this table can supply ``prop`` for. Membership answers both…, _audit_composites(), _empty() (+100 more)

### Community 2 - "Delivery Refusal Vocabulary"
Cohesion: 0.04
Nodes (100): _check_value(), ColumnSpec, FormulaError, hydride_data_schema(), _load(), load_hydride_data(), load_ml_hydpark(), load_prefeaturized() (+92 more)

### Community 3 - "Leak Sentinels"
Cohesion: 0.04
Nodes (97): _baseline_error(), _baseline_prediction(), _class_frame(), _deployed_fit(), _drop_object_columns(), _explainability_record(), _explanation(), _features() (+89 more)

### Community 4 - "Canonical Composition Key"
Cohesion: 0.04
Nodes (91): delivery_screens(), The screens the delivery path runs, in the order their verdicts are reported.…, Every code an answer may carry: admitted, the screens' declared reasons,…, reason_codes(), _answer(), answers(), baseline(), candidates() (+83 more)

### Community 5 - "Descriptor Feature Contract"
Cohesion: 0.03
Nodes (77): assert_contract(), ContractError, FeatureSpec, _named(), DataFrame, ValueError, The 22 features: their names, their order, their dtype, and where each one is…, A feature matrix, a name or a manifest does not match the contract. A… (+69 more)

### Community 6 - "Keyed Feature Merge"
Cohesion: 0.04
Nodes (73): FixtureRequest, The frame with its canonical key attached and its ``Alloy_class`` reconciled.…, with_metadata(), check_fixture(), _elapsed(), emit(), fixture_schema(), load_fixture() (+65 more)

### Community 7 - "External Libraries and Archival Report"
Cohesion: 0.07
Nodes (72): ValueError, The selector cannot run on what it was given, and the message says why. A…, Choose the feature set, from ``train`` and from nothing else. The three…, Run the selector once per outer fold of card #88's protocol. The protocol shape…, select_across_folds(), select_features(), SelectionError, alloys() (+64 more)

### Community 8 - "Element Mover's Distance Novelty"
Cohesion: 0.06
Nodes (58): _coverage(), Raw against calibrated, over the calibration rows, in weight percent. Both…, _assert_parity(), calibrated_heads(), compare_metrics(), conformal_from(), ConformalError, _extract_correction() (+50 more)

### Community 9 - "Surrogate Prediction Interface"
Cohesion: 0.05
Nodes (52): AC-1 -- the same seed reproduces identical metrics. PRD section 10.1: the…, The gate. It fits two models and compares what they are worth, never their…, SeedReproducibility, ConformalCoverage, AC-3 -- conformal interval coverage matches its nominal level. PRD section…, The gate. Every number it reports is measured in this call., KnownAlloyRoundTrip, AC-4 -- known training alloys round-trip through the screening path. PRD… (+44 more)

### Community 10 - "Feature Selection Inside Folds"
Cohesion: 0.06
Nodes (54): _distribution_version(), environment(), Git, Manifest, ManifestError, now(), PayloadRecord, Any (+46 more)

### Community 11 - "Smoke Pipeline Fixture"
Cohesion: 0.09
Nodes (66): current(), load(), The promoted version, or ``None`` if nothing has been promoted yet., Load an artifact version, with everything it recorded about itself. Args:…, Write a new artifact version and return the manifest recorded beside it. Args:…, save(), contract(), green() (+58 more)

### Community 12 - "Screen Protocol Runner"
Cohesion: 0.05
Nodes (62): emit(), Measure the reference from the curated data's **training** split. The slow…, capacity_contender(), capacity_matrix(), Configuration, loss_function(), ModelSettings, _optuna() (+54 more)

### Community 13 - "Delivery Contract Types"
Cohesion: 0.06
Nodes (63): alloy_class_table(), alloy_classes(), CanonicalisationError, group_keys(), _named(), DataFrame, Series, ValueError (+55 more)

### Community 14 - "Quantile Model Fitting"
Cohesion: 0.06
Nodes (61): re, build_cbfv_reference(), build_cbfv_statistics(), build_jarvis(), build_oliynyk(), _cell(), _column_index(), main() (+53 more)

### Community 15 - "Leak Inventory"
Cohesion: 0.06
Nodes (54): argparse, GateReport, LookupError, Every registered gate, ordered by name. Discovery happens once per process., Choose gates by name, by lane, or take them all. Raises: UnknownGate: A…, The outcome of one harness run, and the object card #4's manifest embeds., Whether this run may be called green. A skip is tolerated under a broad…, A gate was requested by a name nothing is registered under. (+46 more)

### Community 16 - "Raw Data Loaders"
Cohesion: 0.05
Nodes (57): ElementDataError, load_table(), ndarray, Path, ValueError, The numeric element properties, and where each one came from. Card #16. This…, One number, or an exception that says exactly what is missing. Never returns…, ``prop`` for each element, in the order given. The array is what the… (+49 more)

### Community 17 - "Descriptor Computability"
Cohesion: 0.06
Nodes (54): The binomial standard error of a coverage estimate over ``n`` independent rows.…, _standard_error(), str, The four things a gate run can honestly say. ``SKIPPED`` is not a mild pass. It…, Status, pointed_at(), Path, A factory: save a :class:`~hydms.surrogate.deploy.DeployedFit`, get a… (+46 more)

### Community 18 - "Gate Harness Registry"
Cohesion: 0.08
Nodes (53): apply_screens(), ValueError, A screen broke the contract, or the runner was given something it cannot…, Run every screen over the whole batch and collect one verdict table. Args:…, ScreenError, batch(), Custom, FakeScreen (+45 more)

### Community 19 - "Conformal Calibration"
Cohesion: 0.06
Nodes (51): Finding, label_issues(), MALFORMED_FORMULAE, _named(), DataFrame, Series, ValueError, L1 -- which **training** rows are suspect, and the record of what was removed.… (+43 more)

### Community 20 - "Artifact Manifest"
Cohesion: 0.06
Nodes (57): answer_from(), DomainVerdict, Answer, One screen's answer about this candidate, carried verbatim into the result. The…, Whether this candidate is one the model may be asked about, and why. The second…, The admitted verdict, with one passing :class:`ScreenVerdict` per named screen.…, An answer with no number in it, and a stated reason for that. A refusal is a…, Always ``True``. A property, not a field, so it cannot be set to the wrong… (+49 more)

### Community 21 - "Surrogate Training Run"
Cohesion: 0.06
Nodes (57): calibration_groups(), calibration_slice(), Hashable, Split training rows into the rows the model grows on and the rows that…, Assert no canonical composition spans the two sides of a calibration carve.…, fitted(), One fitted model and its calibration, over the fixture corpus., _settings() (+49 more)

### Community 22 - "Calibrated Quantile Heads"
Cohesion: 0.06
Nodes (54): The train/val/test protocol. Fractions are 0.20 / 0.10 as `split_data.py`…, Split, assign_splits(), _cut(), _group_statistics(), _merge_rare_strata(), Any, DataFrame (+46 more)

### Community 23 - "Applicability Domain Screen"
Cohesion: 0.05
Nodes (42): Computability, FeatureContract, Hole, Any, Every element ``table`` can supply ``prop`` for. A one-line forward to…, One reason one feature cannot be computed for one composition. Carries the…, Which of the contract's features this composition can actually produce. The…, Whether every feature in the contract can be computed for this composition. (+34 more)

### Community 24 - "Artifact Store Promotion"
Cohesion: 0.05
Nodes (50): L0 -- the leak sentinels: the guarantee that a leak this phase removed stays…, by_id(), Leak, The thirteen named leaks, as data. ``docs/PHASE-H-RUNBOOK.md`` section 1 is the…, Look one leak up by its id. Raises: KeyError: No such leak. Loud on purpose: a…, One row of the runbook's leak inventory. Attributes: id: ``"L1"`` .. ``"L13"``.…, Deferral, _demonstrate() (+42 more)

### Community 25 - "Grouped Data Splits"
Cohesion: 0.08
Nodes (49): _columns(), final_fit(), fit_quantile_model(), _FoldRows, model_from(), ModelError, _named(), _owned() (+41 more)

### Community 26 - "Gate CLI Reporting"
Cohesion: 0.06
Nodes (49): Any, L3 — the surrogate's public interface: formulas and temperatures in, a…, One artifact version, ready to answer, with nothing of its machinery reachable.…, The columns this version featurises and predicts from, in fitting order., The nominal coverage the band targets — ``conformal.confidence_level``.…, Assemble a :class:`Surrogate` from an already-loaded artifact bundle. The whole…, Surrogate, surrogate_from() (+41 more)

### Community 27 - "Acceptance Criteria Gates"
Cohesion: 0.09
Nodes (52): merge_features(), Attach every block to ``spine`` by key, preserving its rows exactly. The result…, block(), jarvis(), oliynyk(), DataFrame, L1 -- the keyed merge that replaces the positional concat. Card #10. Four…, Name the damage in the units of the problem, not just the detection.… (+44 more)

### Community 28 - "Target"
Cohesion: 0.08
Nodes (49): _apply(), _expm1(), Any, Series, ValueError, L1 -- the modelled target is ``log1p(wt%)``, and this is the only module that…, A value cannot be moved between the two target spaces, and the message says…, The weight-percent heading for a model-space column. Never refuses. A model… (+41 more)

### Community 29 - "Composites"
Cohesion: 0.07
Nodes (47): Composite, composite_properties(), CompositeError, decompose(), Disagreement, disagreements(), ValueError, How two element properties combine into one derived property -- and who did the… (+39 more)

### Community 30 - "Applicability"
Cohesion: 0.07
Nodes (47): ApplicabilityDomain, The applicability-domain ceiling, as a :class:`~hydms.screens.protocol.Screen`.…, Every code this screen can emit. Five rejections and the shared indeterminate., The capacity level above which the corpus holds one family. Weight percent., candidates(), DataFrame, parametrize, L4 -- the applicability-domain ceiling. Card #48. ``docs/QA-PROTOCOL.md`` names… (+39 more)

### Community 31 - "Benchmark"
Cohesion: 0.06
Nodes (39): _best(), candidates(), machine(), main(), measure(), Measurement, How many candidate compositions this layer can featurise per second, and where…, The fraction of the wall clock spent in Python parsing formula strings. (+31 more)

### Community 32 - "Harness"
Cohesion: 0.09
Nodes (34): Config, The whole configuration. Immutable, validated, with absolute paths., _band(), The names of the outer two heads, taken from the correction that widened them.…, GateResult, Execute the given gates and collect their results. No gate can end this call…, What one gate concluded, in a shape that survives a JSON round trip.…, run() (+26 more)

### Community 33 - "Stats"
Cohesion: 0.05
Nodes (46): CompositionError, ValueError, A batch of compositions cannot yield a statistic, and the message says why. A…, _cbfv_oliynyk(), oliynyk_reference(), pack(), ndarray, parametrize (+38 more)

### Community 34 - "059 Pymoo Problem Definition"
Cohesion: 0.07
Nodes (47): Card 38: ML-HydPARK thermodynamic loader, ML-HYDPARK v0.0.5 thermodynamic subset (772 complete rows, 744 formulae), Card 39: Parameterise surrogate training by target, Target as a config key, not a second training script, Card 40: Train the enthalpy and entropy surrogates, Witman et al. pretrained thermodynamic models (rejected as a dependency), Card 41: GATE AC-5 — predicted entropy clusters near -130 J/(mol H2 K), ΔS ≈ -130 J/(mol H2 K) physics invariant (+39 more)

### Community 35 - "Contract"
Cohesion: 0.09
Nodes (27): _code(), ContractError, _finite(), _named(), Novelty, Any, ValueError, L6 -- the vocabulary every consumer of a prediction speaks. Three consumers are… (+19 more)

### Community 36 - "L3 L10 Holdout Immutability"
Cohesion: 0.08
Nodes (43): assert_holdout_unchanged(), _fingerprint(), LeakDetected, _named(), Any, Hashable, The mechanical guards behind the leak sentinels. Eight functions, each…, Select ``labels`` from ``table``, refusing a duplicated label. A duplicated… (+35 more)

### Community 37 - "Window"
Cohesion: 0.07
Nodes (38): L4 — physics windows, the applicability-domain ceiling, novelty and cost. A…, _number(), DataFrame, L4 -- the simplest admissibility rule there is: a number inside a closed…, Two codes: outside the interval, and no number to compare., The interval as it appears in every reason this screen writes., A verdict per candidate: inside, outside, or unreadable. Raises: ScreenError:…, The trained temperature range, from config -- the outer bound of the refusal… (+30 more)

### Community 38 - "Model"
Cohesion: 0.08
Nodes (41): Hyperparameter, quantile_metrics(), What one fit's predictions are worth, in weight percent. All of it in weight…, One dimension of the Optuna search, as data rather than as a ``suggest_`` call.…, Ask a trial for a value. The only place this module calls Optuna's API., _frame(), _predicted(), DataFrame (+33 more)

### Community 39 - "L11 Explainability"
Cohesion: 0.08
Nodes (41): assert_explanation_is_not_held_out(), An explainability record must say what it ran on, and it must not be a held-out…, audit(), for_leak(), _module_exists(), The sentinel guarding one leak, or ``None`` if it is deferred., Whether ``dotted`` is importable, without importing it. A missing leaf under an…, Check every leak in the inventory, in inventory order. One row per leak, saying… (+33 more)

### Community 40 - "Protocol"
Cohesion: 0.07
Nodes (32): _check_screen(), _check_verdict(), _column(), _fingerprint(), _named(), Any, DataFrame, Index (+24 more)

### Community 41 - "Config"
Cohesion: 0.10
Nodes (40): load(), Load, validate and return the configuration. Args: path: A YAML file. Defaults…, Locate the repository root for this checkout. Resolution order, most explicit…, repo_root(), cfg(), MonkeyPatch, parametrize, Path (+32 more)

### Community 42 - "Promote"
Cohesion: 0.12
Nodes (40): main(), _parser(), ArgumentParser, TextIO, Path, Card #34 — certifying a candidate version, and refusing to when it is not…, Two hops from a promoted model to the commit that fitted it, neither inferred., Recorded as a test because it is the finding, not a limitation of the command.… (+32 more)

### Community 43 - "Metadata"
Cohesion: 0.08
Nodes (35): MetadataError, ValueError, Metadata is missing where it is needed, or present where it must not be. A…, The record and the feature matrix, side by side, joined by **label**. The other…, with_features(), parametrize, L1 -- the metadata boundary, and the alloy class that has to cross it. Card…, ``Ce1Mg12`` is ``MIC`` in the file and ``Mg12Ce1`` is ``Mg``. A fold that holds… (+27 more)

### Community 44 - "Validation"
Cohesion: 0.09
Nodes (39): alloys(), _folds(), Any, DataFrame, L3 -- the folds group on the material, and nothing scores on what it was chosen…, A split assignment that holds the last twenty rows out, so `nested_scores` will…, The real 1,279 rows and card #13's split assignment, computed once., `grouped_folds` with the fixture's bin counts, so a test says only what it… (+31 more)

### Community 45 - "Comparison"
Cohesion: 0.08
Nodes (35): date, ComparisonError, _features(), Placeholder, placeholder_exposure(), Path, Series, ValueError (+27 more)

### Community 46 - "Store"
Cohesion: 0.10
Nodes (36): Exception, L0 — the versioned artifact store and its manifest. The only way a model,…, ArtifactError, Base for every refusal from :mod:`hydms.artifacts`., _check_waivers(), GatesIncomplete, PayloadCorrupt, LookupError (+28 more)

### Community 47 - "Validation"
Cohesion: 0.14
Nodes (38): Contender, grouped_folds(), nested_scores(), SplitSettings, ``StratifiedGroupKFold`` over the canonical compositions of ``frame``. The…, Everything the hyperparameter search is allowed to see, and nothing else.…, The one fit that is scored: refit on the outer fold's training rows, scored on…, One model in the comparison: how it is tuned, and how it is scored. Two… (+30 more)

### Community 48 - "Deploy"
Cohesion: 0.10
Nodes (34): _cost(), _destination(), main(), _parser(), ArgumentParser, DataFrame, Path, TextIO (+26 more)

### Community 49 - "Cleanlab"
Cohesion: 0.15
Nodes (19): boruta, catboost, cleanlab.regression.learn, joblib, matplotlib.pyplot, numpy, optuna, os (+11 more)

### Community 50 - "Novelty"
Cohesion: 0.10
Nodes (32): ElementMoversDistance, Measure every candidate's chemical distance to the nearest known alloy. Every…, Two codes: past the corpus's internal spread, and a formula ElMD cannot read., The distance past which this screen refuses. See the module docstring., _candidates(), DataFrame, parametrize, AC-7 is a reporting obligation: a rejected candidate still carries its number. (+24 more)

### Community 51 - "L1 L5 Early Stopping"
Cohesion: 0.07
Nodes (32): assert_early_stopping_is_honest(), The rows that choose the stopping iteration may not be the rows that score it.…, _l1_empty_eval_set(), _l1_eval_set_is_the_test_pool(), _l1_eval_set_is_the_validation_split(), _l5_fold_stops_on_an_inner_slice(), _l5_fold_stops_on_itself(), `Catboostmodel.py:604-606` -- final_model.fit(..., eval_set=test_pool). (+24 more)

### Community 52 - "L2 L4 Model Selection"
Cohesion: 0.11
Nodes (33): assert_selection_is_nested(), What one candidate model contributed to the model-selection decision. Card…, Model selection may not see a held-out metric, nor score on the folds it tuned…, SelectionRecord, _l2_live(), _l2_record_without_a_test_metric(), _l2_test_metric_in_the_record(), _l4_live() (+25 more)

### Community 53 - "Domain"
Cohesion: 0.08
Nodes (29): applicability_domain(), DomainReference, emit(), main(), _number(), Series, TextIO, L4 -- how far from known chemistry a prediction may be trusted. The card asked… (+21 more)

### Community 54 - "Selection"
Cohesion: 0.10
Nodes (32): _boruta(), _candidates(), _factor(), _named(), Any, DataFrame, Hashable, Series (+24 more)

### Community 55 - "014 Cleanlab Screening As"
Cohesion: 0.07
Nodes (34): Card 13: Stratified unique-formula splits, seeded and reproducible, Leak L8: splits grouped on the raw formula string, Measured split 893 / 131 / 255 over 780 / 111 / 224 compositions, Three physically impossible curated rows (H/M above ceiling), Card 14: CleanLab screening as a data-layer stage, Leak L10: held-out features clipped by their own residuals, Leak L12: target-conditioned sample weights, Leak L3: held-out labels overwritten by the model's own predictions (+26 more)

### Community 56 - "Ac4 Round Trip"
Cohesion: 0.09
Nodes (26): _features(), Any, DataFrame, Hashable, Series, ``wanted`` rows the model grew on, taken from as many alloy classes as…, Per-feature values from both paths, for the card's "diagnosable" box. Computed…, _spread() (+18 more)

### Community 57 - "Comparison"
Cohesion: 0.10
Nodes (30): comparison(), published(), Path, L3 -- the old 22 against the declared set, and the guards that keep the story…, `voro_coord` is filler for two elements; only one of them is in the dataset.…, `SELECTED` is what every fold chose -- names *and* order. This is the guard…, The candidate pool is the published 22, so old-versus-new is a subset relation., Regenerate and compare. A hand-edited paragraph of numbers goes red here. The… (+22 more)

### Community 58 - "Merge"
Cohesion: 0.13
Nodes (28): _addressed(), FeatureBlock, MergeError, _named(), _null_mask(), Any, DataFrame, Index (+20 more)

### Community 59 - "L12 Sample Weights"
Cohesion: 0.12
Nodes (29): assert_weights_ignore_target(), Sample weights may be computed from the rows' features; never from their…, _frame(), DataFrame, leak, L12 -- a row may not be weighted by its own answer.…, The case the rescale exists for, and the one a shuffle alone cannot see. Every…, A check against a column that is not there passes vacuously, which is the… (+21 more)

### Community 60 - "Novelty"
Cohesion: 0.12
Nodes (27): float64, distances(), _elmd_class(), _named(), Any, DataFrame, NDArray, L4 -- how chemically far a candidate is from everything already known. PRD 4.3… (+19 more)

### Community 61 - "L7 L8 Grouping"
Cohesion: 0.10
Nodes (28): assert_disjoint_groups(), No group key may appear in more than one partition. Guards **L8**…, _l7_a_formula_in_two_folds(), _l7_folds_grouped_by_composition(), _l7_live(), _l8_one_composition_in_two_splits(), _l8_splits_grouped_by_composition(), `benchmark_model_selection.py:895` -- StratifiedKFold over rows, with no groups. (+20 more)

### Community 62 - "Validation"
Cohesion: 0.11
Nodes (28): _assemble(), _averaged(), _complete(), _discard(), _keeper(), leave_one_class_out(), _metrics(), _named() (+20 more)

### Community 63 - "Conftest"
Cohesion: 0.09
Nodes (28): hydride_raw(), known_collisions(), Path, Shared fixtures for the hydms test suite. Two rules shape this file: -…, The repository root, so no test needs a relative path or a `cwd` assumption., Path to the raw dataset, skipping the test if it is not in this checkout., The raw dataset, read once per session. Private: use `hydride_raw` for a safe…, A fresh copy of the raw dataset (1279 x 6), safe to mutate. Columns:… (+20 more)

### Community 64 - "L9 Keyed Merge"
Cohesion: 0.14
Nodes (26): assert_merge_is_keyed(), A merge must join on a key, not on row position. Guards **L9**…, frames(), keyed_join(), positional_concat(), Any, DataFrame, L9 -- the merge joins on a key, or it silently attaches features to the wrong… (+18 more)

### Community 65 - "Predict"
Cohesion: 0.11
Nodes (26): predict(), Path, Calibrated maximum-capacity intervals for a batch of candidate alloys. The deep…, fitted(), _forget_between_tests(), The surrogate's public interface: what comes back, what stays hidden, what it…, One fitted model, its calibration and a scaler over the same columns. Module-…, The loader caches by (store, version); a fixture that writes a new store must… (+18 more)

### Community 66 - "Golden"
Cohesion: 0.10
Nodes (26): diff(), measure(), measure_deployed_screening(), modelling_contract(), slow, L1 -- one pinned record of what the data layer produces. Card #15. Every other…, The 21-feature contract the modelling matrix is built from. ``COSTLY_FEATURE``…, Run the data layer end to end and record what it produced. (+18 more)

### Community 67 - "L13 Class Survival"
Cohesion: 0.15
Nodes (25): assert_metadata_survives(), A stage may add columns and compute features; it may not lose the ones it was…, _l13_live(), Card #12's join, against the real dataset: the class arrives on the other side.…, archival_featurisation(), honest_featurisation(), DataFrame, L13 -- a column that is not a feature is still not disposable.… (+17 more)

### Community 68 - "Evaluate"
Cohesion: 0.13
Nodes (23): _asserted(), EvaluationError, _heads(), pdp_table(), DataFrame, ValueError, L3 -- what the model is worth, with an interval on every number and a name on…, A table cannot be read, or does not carry what a metric needs. A… (+15 more)

### Community 69 - "Evaluate"
Cohesion: 0.11
Nodes (25): main(), _parser(), ArgumentParser, Path, TextIO, Read the tables, put an interval on every number, and report. Returns the exit…, The row-level predictions a nested run wrote, checked for what a metric needs.…, What kind of run wrote these tables, as a phrase for the ``run`` column.… (+17 more)

### Community 70 - "Ac2 Parity"
Cohesion: 0.09
Nodes (24): cbfv(), cfg(), passing(), _perturbed(), MonkeyPatch, Card #21 — the parity gate, and the four things it has to get right. 1. **It…, Not only on failure. A pass that cannot say where it came closest is not…, A featuriser that is wrong by `offset` in one column, for one composition. (+16 more)

### Community 71 - "Phase H Runbook"
Cohesion: 0.10
Nodes (25): early_stopping_rounds is a wall-time multiplier, not a model choice, assert_disjoint_groups, assert_early_stopping_is_honest, assert_explanation_is_not_held_out, assert_holdout_unchanged, assert_metadata_survives, assert_selection_ignores_holdout, assert_selection_is_nested (+17 more)

### Community 72 - "Inverse Design Methods"
Cohesion: 0.09
Nodes (25): Wilson et al. 2024 - HyStor Database, HyStor Experimental Database, Kauwe et al. - CBFV, Future Directions, HydMS Project Report, Wilson et al. 2024 - HyStor Database, Choudhary et al. 2020 - JARVIS, ML-HYDPARK v0.0.5 Benchmark Dataset (+17 more)

### Community 73 - "016 Element Property Tables"
Cohesion: 0.10
Nodes (24): ndarray, The five statistics of one property over a batch of compositions. Every field…, ``stats["avg"]`` -- so the caller can index with the half of a feature name.…, The five statistics of one element property over a batch of compositions. Args:…, Statistics, scripts/build_element_tables.py — the derivation audit trail, Card 16: Element property tables with cited provenance, CBFV carries no licence and cannot be vendored (+16 more)

### Community 74 - "L6 Selection Independence"
Cohesion: 0.14
Nodes (24): assert_selection_ignores_holdout(), Perturbing the held-out rows must not change the selected feature set. Guards…, Any, DataFrame, L6 -- feature selection must be blind to the rows it does not own.…, A failure a reviewer cannot reproduce is a failure that gets dismissed., The detector perturbs a copy. A detector that damages its input is used once., Nothing could be perturbed, so the check would pass whatever the selector does. (+16 more)

### Community 75 - "Scaler"
Cohesion: 0.12
Nodes (25): fit_scaler(), Series, Fit the scaling transform on one split of a feature matrix. The split is a…, Series, `refuse_non_features` runs at fit time, where the feature set is established., `temperature(K)` is a raw column and a feature; a positional concat returns it…, The fit only reads the training rows, so only those can stop it., `RobustScaler` substitutes 1.0 for a zero span, so 1.0 alone cannot be read… (+17 more)

### Community 76 - "Scaler"
Cohesion: 0.12
Nodes (23): FittedScaler, A fitted robust scaling transform, with no way to fit it again. Constructed…, How many features it scales., DataFrame, parametrize, The AC-4 failure mode, closed: the caller's order does not reach the model., scikit-learn accepts one with a UserWarning; that is the door this closes., The defect memo 4.3 names: a candidate scored differently for its company. (+15 more)

### Community 77 - "Report"
Cohesion: 0.10
Nodes (23): Models Evaluated Table, bootstrap_ci(), evaluate_model(), optuna_stacking_objective(), weighted_score(), evaluate_model(), optuna.pruners, optuna.samplers (+15 more)

### Community 78 - "Requirements Lock"
Cohesion: 0.09
Nodes (24): Extras policy: parity excluded, uq and novelty installed, CI job: suite (pytest and the fast gates), The two-stage rebuild (conda, then pip --no-deps), scripts/verify_environment.py, CatBoost MultiQuantile, ConformalizedQuantileRegressor with prefit=True, ElMD 0.5.15 — Element Mover's Distance, MAPIE 1.x conformal API (+16 more)

### Community 79 - "Report"
Cohesion: 0.11
Nodes (24): Ask the Graph Before You Grep, Inverting the Descriptors (rejected alternative), The Enabling Fact (all 22 features are composition statistics plus temperature), Descriptor Non-Invertibility, Graph Query - Why the Inverse Design Methods Memo Bridges Into CBFV Featurisation, Feature Category Correlation Analysis, Expanded Material Science Linkage Summary, Mutual Information vs Pearson Analysis (+16 more)

### Community 80 - "Metadata"
Cohesion: 0.12
Nodes (23): Columns, The column names in the raw dataset, which are not identifiers and contain…, metadata_columns(), _named(), non_feature_columns(), L1 -- the columns that are the record, not the model's input.…, Render offenders for a message: sorted, truncated, and counted., The columns a featuriser must carry through, in the order they appear in the… (+15 more)

### Community 81 - "Loco"
Cohesion: 0.16
Nodes (23): _budget(), _chosen(), _destination(), _emit(), main(), _parser(), ArgumentParser, DataFrame (+15 more)

### Community 82 - "No Leak"
Cohesion: 0.15
Nodes (23): _frame(), DataFrame, The test split is named by every fit and read by none of them -- leaks L1 and…, `eval_set=test_pool`, reintroduced against the real fit. This is the…, Half the test set is not half a leak; the whole validation split or nothing., CatBoost refuses this at fit time; the point is that it refuses here first. The…, Cruder than L1, and not L1: a `ModelError`, so a raised `LeakDetected` always…, Early stopping that watches rows the trees are growing on never fires. Not in… (+15 more)

### Community 83 - "Init"
Cohesion: 0.10
Nodes (21): _build(), ConfigError, Conformal, Domain, Model, Paths, Any, Path (+13 more)

### Community 84 - "Ac1 Reproducibility"
Cohesion: 0.13
Nodes (20): _differences(), Any, Every number that moved, as ``(name, first, second, gap)``. The metrics *and*…, parametrize, slow, Card #32 — the reproducibility gate, and the decision it is built on. The…, A fit that stopped elsewhere and scored the same is reproducible by accident.…, ``r2`` is NaN when the truth has no variance, and NaN != NaN would report that… (+12 more)

### Community 85 - "Inverse Design Methods"
Cohesion: 0.10
Nodes (23): Split Data Summary, Unique-Formulae Split Basis (1149 of 1279), get_temp_group(), Stratified Dataset Splits (896/136/247), Model Limitations, Temperature Subgroup Performance, Applicability Domain and Novelty Control, Baird et al. 2022 - DiSCoVeR (+15 more)

### Community 86 - "Phase H Runbook"
Cohesion: 0.13
Nodes (21): CI step: hydms.gates run --fast, HG-1 — Leak sentinels gate, HG-2 — No bare numbers gate, HG-3 — Transport parity gate, hydms.artifacts.save / load — the versioned artifact store, hydms.delivery.api — FastAPI transport, hydms.delivery.contract — PredictionResult and Refusal, hydms.delivery.predict — predict_capacity(), the deep module (+13 more)

### Community 87 - "Old Vs New"
Cohesion: 0.13
Nodes (22): The consensus 14 feature set, Card #83: Model-card page — honest metrics and stated limits, The per-row calibrated interval width distribution, The near-ambient temperature bin is the weakest, Three R² readings, and a sentence saying which is which, Card #89: REPORT.md versus the artifacts it cites, Eu1Ni5: a corrupted row in the published feature matrix, §4.2's Overfitting footnote mixes two target spaces (+14 more)

### Community 88 - "Contract"
Cohesion: 0.10
Nodes (18): Interval, A calibrated prediction interval, in weight percent, with the level it targets.…, ``upper - lower``, in :data:`UNIT`. Computed rather than stored, so it cannot…, Whether ``value`` lies inside the closed band., The interval as JSON-ready primitives, ``width`` included for a reader., Rebuild an interval. ``width`` is ignored: it is derived, and derived twice is…, parametrize, The refusal is on `Interval`, which is why the result's own cross-check never… (+10 more)

### Community 89 - "Cli"
Cohesion: 0.17
Nodes (21): main(), _parser(), ArgumentParser, One line for a CI step summary or a commit comment., summarise(), CaptureFixture, Path, Tests for `python -m hydms.gates`. The exit code is the whole contract as far… (+13 more)

### Community 90 - "Novelty"
Cohesion: 0.13
Nodes (20): Rebuild one, refusing a file this module was not written against., _corrupt(), L4 -- the Element Mover's Distance novelty screen. Card #49. ``docs/QA-…, ``vectors`` sums the parsed counts itself; this pins that it is still ElMD's…, ElMD's own ``ratio_vector`` does not, and that made ``--emit`` irreproducible.…, The premise of the guard below, and the reason a sum-to-one check cannot be it.…, numpy would put ``-1`` at slot 102 and relabel the element without a word., A row summing to anything but one still yields finite distances to everything. (+12 more)

### Community 91 - "090 The Refusal Catalogue"
Cohesion: 0.13
Nodes (22): Card #80: API reference documentation, docs/API.md, Refusal versus a genuinely low prediction, The prediction assembly order, Card #85: ADR — the delivery seam, The library owns no I/O: predict_capacity() is pure, One cache or two: the delivery bundle and the memoised surrogate, Card #90: The refusal catalogue (+14 more)

### Community 92 - "Prd Inverse Design"
Cohesion: 0.10
Nodes (21): The Evaluator Is the Deep Module, Search Is a Seam, Coverage, AC-2 - Featuriser Matches CBFV to 1e-9, AC-3 - Conformal Coverage Within a Few Points of Nominal, Acceptance Criteria AC-1 to AC-8, Angelopoulos & Bates 2023 - Conformal Prediction: A Gentle Introduction, Architecture A - Screen-and-Rank, Architecture B - Constrained Multi-Objective EA (pymoo NSGA-II) (+13 more)

### Community 93 - "Sources"
Cohesion: 0.12
Nodes (21): AC-2 — CBFV parity to 1e-9, hydms.data.metadata — metadata vs non-feature columns, hydms.descriptors.contract — CONTRACT (22) and SELECTED (14), hydms.descriptors.featurize — the layer's public interface, hydms.pipeline.smoke — the 12 s chain check, S3 — Descriptor layer, columns: Composition, Alloy_class, Dataset, H2_W% (max), temperature(K), Citation, scripts/build_element_tables.py (+13 more)

### Community 94 - "Canonical"
Cohesion: 0.10
Nodes (21): canonical_key(), The identity of the material ``formula`` describes. Two strings receive the…, parametrize, The regression fixture: six pairs the audit found spanning two splits. Two by…, It reads as chemistry, not as a hash -- and `parse_formula` can read it back., A key is a label, not an input, and this is the guard on saying so. Rounded…, `co` is `Co`, or `C` and `O`, and nothing here can tell which. Both shapes of…, A key naming an element at zero would claim a composition nobody wrote.… (+13 more)

### Community 95 - "Scaler"
Cohesion: 0.16
Nodes (20): ValueError, The scaler cannot be fitted, or is being asked to transform the wrong matrix. A…, ScalerError, _fitted(), matrix(), L3 -- the scaler is fitted once, on train, and can never be fitted again. Card…, The guard that stops "fit on train" from being satisfied by relabelling., Paired by label, never by position -- leak L9 in a new place. (+12 more)

### Community 96 - "Hydride Domain Grounding"
Cohesion: 0.11
Nodes (21): The band is wide relative to the physics, The material-versus-system caveat, The enabling fact survives the re-selection, Angelopoulos & Bates 2023 — Conformal Prediction: A Gentle Introduction, Beltrame et al. 2025, Metals 15, 1221, What composition-based features cannot encode, Conformal prediction for distribution-free intervals, Cross-family generalisation fails (+13 more)

### Community 97 - "Novelty"
Cohesion: 0.13
Nodes (16): novelty_screen(), NoveltyReference, The known chemistry a candidate is measured against, and the bound it may not…, The reference as the committed file, sparse and deterministic. Sparse because a…, The committed reference. What every screen built without one reads., Derive one from a set of known formulas. See :func:`emit` for the real caller.…, The novelty screen over the committed reference, reading the configured formula…, The cross-check must refuse nothing real, or ``--emit`` would move the… (+8 more)

### Community 98 - "Hg2 Refusal Path"
Cohesion: 0.15
Nodes (17): Any, GateResult, Answered, _exits(), _lines(), _named_codes(), Probe, _probes() (+9 more)

### Community 99 - "Context"
Cohesion: 0.12
Nodes (19): Project Conda Environment Interpreter, Artifact Bundle (hydms.delivery.predict.ArtifactBundle), Artifact Version, Deployed Fit, Promotion, Sentinel, Sentinel Subject, Waiver (+11 more)

### Community 100 - "Refusals"
Cohesion: 0.12
Nodes (19): Applicability Domain (a verdict, not a distance), Candidate, 5.19 wt% Capacity Level (domain ceiling), Novelty (distance to nearest known alloy), Three Cards Pulled Out of the Freeze (#44, #48, #49), Baird et al. 2022 - DiSCoVeR, ElMD Novelty to Nearest Known Alloy, apply_screens (+11 more)

### Community 101 - "077 Gate Hg 2"
Cohesion: 0.13
Nodes (19): Lower Confidence Bound (the ranking signal), Prediction (estimate plus interval plus domain verdict), LCB Ranking (rank on the lower confidence bound), Risk R1 - The Optimiser Exploits Surrogate Extrapolation, Contract Test, L6 Delivery Layer Guarantees, indeterminate (reason code), One Sentence This Page Cannot Show (+11 more)

### Community 102 - "Phase H Runbook"
Cohesion: 0.15
Nodes (19): bagging_temperature is inert unless bootstrap_type is Bayesian, AC-6 — Leave-one-alloy-class-out reported beside the random split, The deployed fit was two different models (873 vs 701 rows), hydms.data.canonical — the canonical composition key, hydms.data.screening — CleanLab on training rows only, hydms.data.splits — 893/131/255 grouped split, hydms.surrogate.deploy — the single definition of the deployed fit, hydms.surrogate.loco — leave-one-alloy-class-out run (+11 more)

### Community 103 - "Hg2 Refusal Path"
Cohesion: 0.12
Nodes (17): Findings about the contract types: a bare number must be unspellable. Returns:…, _structural(), _Defaulted, Card #77 -- the gate the whole phase exists for, and the six ways it has to go…, A probe with no stated purpose cannot fail; it can only be re-labelled (card…, A result type whose interval may be omitted -- the bare number, arriving by…, A refusal carrying a capacity "for reference" -- the bare number with a…, A prediction path with a branch that falls out silently. (+9 more)

### Community 104 - "Comparison"
Cohesion: 0.13
Nodes (9): Comparison, Everything the old-versus-new write-up says, assembled from the run's own…, How many outer folds the run cut., What the folds were offered: every feature any fold could have chosen., The features at least ``at_least`` folds selected, in the first fold's order.…, Every fold's answer: the reading this card publishes., The published feature that makes the most rows unfeaturisable., How many training rows the whole-split pass was entitled to. (+1 more)

### Community 105 - "048 Applicability Domain Ceiling"
Cohesion: 0.12
Nodes (19): Optimise in composition space; never invert descriptors, Chapter 1 revision: what exists, what was wrong, what it is now, Ranked composition-only future-work programme (Miedema, H/M, proxies, base learner), Leak L9: positional concat at merge_datasets.py:46 invalidates the Miedema result, Decide the whole change set first; run LOCO once, Mg fails by construction: trees cannot predict above the trained range, Sloping PCT plateaus: pressure is the unobserved confounder, ABOVE_PHYSICAL_CEILING — a separate code from OUT_OF_DOMAIN (+11 more)

### Community 106 - "Hg2 Refusal Path"
Cohesion: 0.11
Nodes (19): Config, The card's "asserted exhaustively, not sampled": the count is of returns, not…, Never a bare number" is satisfied trivially by never answering. That is not a…, Not "a code is missing" -- "a code is missing and nothing in the repo says why"., AC-7 answered with a blank is the failure only a deployment would have shown…, #49's defect: the right code with a sentence that no longer says what it is…, Every ``names`` string is a substring of its own probe's formula, so the check…, The same pin ``tests/gates/test_artifact.py`` holds for AC-3 and AC-4, one… (+11 more)

### Community 107 - "Readme"
Cohesion: 0.14
Nodes (18): Authority Order, HydMS Working Brain (router CLAUDE.md), Nothing Is Trained Invariant, Session Anti-Patterns, As Published, CleanLab.py:90 Overwrites Held-Out Ground Truth, Implementation Freeze - Phase H, The Pipeline Cannot Be Run End to End (+10 more)

### Community 108 - "Validation"
Cohesion: 0.12
Nodes (9): Fold, FoldSet, Any, One train/test partition of a frame, addressed by what it holds out.…, An ordered partition of one frame, with its own disjointness already asserted.…, The fold ids, as a :class:`~hydms.qa.detectors.SelectionRecord` wants them., Fold name -> the keys it holds out, ready for…, The inner folds, recording which of them were read. So that ``tuned_on`` is a… (+1 more)

### Community 109 - "005 Gate Harness Prd"
Cohesion: 0.13
Nodes (18): Lu et al. — 27 unreported alloy compositions, Card #65 — OPTIMADE cross-check for prior art, OPTIMADE federated query (AFLOW, COD, Materials Cloud, Materials Project, NOMAD, odbx, OQMD), A network failure degrades to UNKNOWN, never to NOVEL, Card #4 — Artifact store and manifest contract, FeatureContract.as_manifest() embedded in the model manifest, Every payload carries a SHA-256; load re-hashes and raises PayloadCorrupt, For an artifact, SKIPPED is treated exactly as FAILED (+10 more)

### Community 110 - "Domain"
Cohesion: 0.14
Nodes (15): capacity_ceiling(), _masses(), DataFrame, Index, ndarray, Atomic weights from the same table the featuriser reads. Imported lazily.…, The physical capacity ceiling of each composition, in weight percent. ``wt%_max…, Judge every candidate against every signal its columns support. Raises:… (+7 more)

### Community 111 - "Loco"
Cohesion: 0.18
Nodes (16): document(), _or_absent(), The published write-up, built from the tables and never typed. Generated rather…, A number, or a phrase -- never the string ``nan``. ``summary`` writes NaN when…, Card #30 — leave-one-alloy-class-out, and the ways a per-class table can…, A probe's tables and a real run's tables are the same shape. The difference has…, The rule card #29 established: a published document is generated, never typed.…, A cell reading `nan` invites a reader to treat it as a measurement that came… (+8 more)

### Community 112 - "Loco"
Cohesion: 0.16
Nodes (17): _estimable(), per_class(), Series, One row per alloy class: what it scored, over how much, and whether that means…, Whether a class fold's R2 is a number at all, and if not, why not in words.…, _evaluation(), DataFrame, R2 is a ratio to the total sum of squares, so a constant held-out column makes… (+9 more)

### Community 113 - "Model"
Cohesion: 0.13
Nodes (10): FitLog, FitRecord, Which rows one fit saw in which role, and what the fit cost. The evidence the…, One row of :meth:`FitLog.table`., Every fit a run made, in order. Passed in rather than kept in module state, so…, One row per fit: where it was, how many rows in each role, what it cost., An ndarray carries no column names, so a permuted matrix would be plausible and…, It records identities and reports counts, which is what makes it writable to a… (+2 more)

### Community 114 - "Scaler"
Cohesion: 0.14
Nodes (15): _declared_features(), _named(), L3 -- the scaling transform is fitted once, on the training split, and travels…, Render offenders for a message: sorted, truncated, and counted., The fitted scaler held in a loaded artifact version, checked against its…, The feature names the bundle's manifest records, or ``None`` if it records…, scaler_from(), Any (+7 more)

### Community 115 - "Evaluate"
Cohesion: 0.16
Nodes (16): datetime, _format(), _headline(), A Markdown table of the columns a reader needs, from the frame the CSV carries.…, The same metrics per outer fold and per temperature band, from one split-level…, The published write-up, generated from the tables and from nothing else. Card…, subgroup_table(), _table() (+8 more)

### Community 116 - "Manifest"
Cohesion: 0.16
Nodes (16): describe_git(), digest_file(), Path, Read the current commit and branch at ``root``, and whether its **code** is…, The SHA-256 and byte length of one file. What makes a stored payload checkable.…, Path, An installed package in a container has no work tree. Refusing to save an…, The defect this field was renamed for: a run dirties its own provenance stamp.… (+8 more)

### Community 117 - "Evaluate"
Cohesion: 0.15
Nodes (16): _bootstrap(), Interval, per_fold_intervals(), _percentiles(), ndarray, One metric, its point estimate, and the bootstrap interval around it.…, The two percentile bounds of a replicate distribution, ignoring replicates that…, Every metric with an interval, from one set of replicate index arrays. The… (+8 more)

### Community 118 - "Evaluate"
Cohesion: 0.17
Nodes (16): metrics_table(), R2, RMSE, MAE and the quantile metrics on both scales, each with two intervals.…, _out_of_fold(), DataFrame, AC-1's question, asked of this module. An interval that moves between runs is…, Not the mean of the replicates, and this is the one definition of it.…, R2 on log1p capacity and R2 in weight percent are different claims about the…, Card #29 settled this against prose, and gave the reason: prose is what a… (+8 more)

### Community 119 - "Predict"
Cohesion: 0.14
Nodes (14): _empty_intervals(), DataFrame, Index, ndarray, Series, A calibrated interval per candidate. See :func:`predict`, which delegates here., One row saying which artifact answered and what its band claims. For card #83.…, The calibrated heads, plus the ranking key and the width, in that order. The… (+6 more)

### Community 120 - "Readme"
Cohesion: 0.14
Nodes (16): Card #86: GATE HG-4 — CI fast lane with delivery suite and hygiene, The conda-free hygiene job (ruff and mypy), The coverage floor is currently unenforceable, Whether openpyxl is added, or the HyStor spreadsheet stays unread, The L13 sentinel: Alloy_class survives featurisation, Fifty-five elements, not fifty-four, What a new card must carry, scripts/check_board.py — the board integrity check (+8 more)

### Community 121 - "Report"
Cohesion: 0.12
Nodes (16): Analysis Notebook Suite, SHAP Interpretation Limitations, Non-Standard Formula Inventory, Raw Data Summary (1279 x 6), Shapiro-Wilk Normality Test on H2 wt%, Hydrogen Storage Capacity (H2 wt%), log1p Target Transformation, Matminer Miedema and WenAlloys Features (+8 more)

### Community 122 - "061 Element Subset Outer"
Cohesion: 0.16
Nodes (15): Card #61 — Element-subset outer loop, Fixed element subset per run, swept in an outer loop, hydms.search.sweep, Card #62 — Hypervolume convergence study, Hypervolume versus generation as convergence evidence, pymoo chosen over Optuna's sampler, Card #63 — Multi-seed stability study, Front is a property of the problem, not of the seed (+7 more)

### Community 123 - "034 Train And Publish"
Cohesion: 0.15
Nodes (15): artifacts/v2 — the version to promote, One definition of the deployed fit (hydms/surrogate/deploy.py), python -m hydms.surrogate.promote, --report is also an input path (the CatBoost-defaults trap), The waiver summary counts wrong and no test asserts the string, A waiver is an act, not a property, tests/artifacts/test_waiver_scope.py — waivable set derived from the boards, Sentinel subject — glossary term born of the L11 drift (+7 more)

### Community 124 - "Phase H Runbook"
Cohesion: 0.19
Nodes (14): The python-graphviz export defect, ElMD partial-parse defect — LaNi5Xx2 is LaNi5 at distance 0.0, mod_petti is a closed form: sum(abs(cumsum(a - b))), ratio_vector is not reproducible across processes, assert_merge_is_keyed, hydms.screens.apply_screens — the verdict runner, hydms.screens.domain — the applicability-domain ceiling (5.19 wt%), hydms.screens.novelty — ElMD novelty screen (ceiling 11.7320) (+6 more)

### Community 125 - "Store"
Cohesion: 0.16
Nodes (6): Artifacts, Any, One loaded artifact version: the objects, and the manifest that vouches for…, The payload keys this version holds, in the order they were saved., The columns the stored model was fitted on, in fitting order., The stored :class:`~hydms.descriptors.contract.FeatureContract`, digest checked.

### Community 126 - "033 Gate Ac 4"
Cohesion: 0.14
Nodes (14): Compare like with like: calibrated_heads, not raw heads, GATE AC-4: known alloys round-trip through predict(), Failure output separates column ORDER from a different computation, hydms/gates/_artifact.py: the require_gates=False door for gates, _spread(): deterministic round-robin over Alloy_class, surrogate_from(bundle): assembling split from locating, Column-order independence: _batch selects the fitted names, answer_from() — the one door back from JSON (+6 more)

### Community 127 - "069 Infrastructure Pytest Ruff"
Cohesion: 0.14
Nodes (14): Board and prose integrity check — the fast-lane seed, scripts/check_board.py — ids, statuses, blocker resolution, acyclicity, links, .github/workflows/integrity.yml, Stdlib-only on purpose: it must run when the conda env is broken, Test infrastructure: pytest, ruff, mypy and the coverage floor, Coverage floor fail_under = 80 on hydms/, Legacy Machine_Model tests excluded by configuration, not by rename, The conda-free lint lane: ruff and mypy run outside Project (+6 more)

### Community 128 - "087 Canonical Composition Key"
Cohesion: 0.15
Nodes (14): ALLOY_CLASS_PRECEDENCE: reconcile by precedence, not by majority, canonical_key(): identity insensitive to order, scaling, whitespace and case, Card #87: Canonical composition key and Alloy_class reconciliation, The 1149 → 1142 → 1121 → 1115 collapse, Four significant digits: the resolution the key rounds to, group_keys(): the single grouping seam for splits and folds, Leak L8: splits grouped on the raw formula string, separation(): nothing merged is farther apart than something not merged (+6 more)

### Community 129 - "Running The Fit"
Cohesion: 0.15
Nodes (13): PropertyTable.servable — the memo moved onto the table, The 13x that was hiding (a benchmark of four repeated formulae), CBFV 1.1.0 — unmaintained, breaks under NumPy 2.x, NumPy 1.26.4 / Python 3.10.13 pin (3.13 excluded), The conda environment `Project`, Native TreeSHAP over MultiQuantile via get_feature_importance, hydms.surrogate.evaluate — bootstrap CIs over canonical groups, reports/model/model-chosen.csv — the committed deployed configuration (+5 more)

### Community 130 - "Store"
Cohesion: 0.15
Nodes (13): promote(), Point ``current`` at ``version``, refusing anything its gates did not…, The default promotion is byte-for-byte the one the store made before #34., A no-op waiver would rot the list into decoration, and a decorative list stops…, A typo, or a criterion since renamed. Either would otherwise present as a…, `load()` with no version is the delivery path's call, and it is what the waiver…, test_a_skipped_criterion_can_be_waived_and_the_reason_is_recorded(), test_a_waiver_with_no_reason_is_refused() (+5 more)

### Community 131 - "Loco"
Cohesion: 0.21
Nodes (13): _extreme(), The two averages, the count behind each, and the random-split number beside…, Which class scored worst or best. Empty when nothing was estimable., summary(), Two classes of very different size, so the two averages cannot agree., Which one is larger is a property of the run, not of the design — a sentinel-…, AC-6 is 'reported alongside'. A summary with one number and not the other does…, _summary_table() (+5 more)

### Community 132 - "Predict"
Cohesion: 0.23
Nodes (13): load_surrogate(), The promoted artifact version, loaded and checked, ready to predict from. Args:…, Path, The information-hiding check card #28 sets: swapping the regressor changes…, An artifact version is written once and never edited, so caching by version…, Rollback is a one-line write (card #7). It must take effect on the next…, test_a_version_is_loaded_once_and_held(), test_callers_never_see_the_model_the_scaler_or_the_calibrator() (+5 more)

### Community 133 - "006 Ci Fast Lane"
Cohesion: 0.18
Nodes (13): Card #6 — CI fast lane: lint, tests and gates, The conda-free hygiene job — lint and types build no environment, math.log1p differs by one ulp between MSVC and glibc, environment.lock.yml is win-64 by construction and cannot restore on Linux, A lint lane on a version floor is not a check — ruff pinned exactly, The old push:branches:[main] trigger meant the Phase H branch was never checked, train.py --budget over-projects by ~45 % (scored fits only, no pruning model), Card #7 — CI slow lane: retrain, upload and version promotion (+5 more)

### Community 134 - "073 End To End"
Cohesion: 0.15
Nodes (13): Train and publish the deployed artifact version, A run re-reads pipeline.yaml mid-flight (~2,300 windows), The manifest records the run's own SHA, not promotion-time HEAD, SMOKE_SPLIT and SMOKE_FOREST_TREES — budgets that change how, not which, End-to-end smoke pipeline on a sampled fixture, The fixture is filtered to what the feature contract can serve, smoke-fixture.csv — generated by --emit, shape-checked by check_fixture(), python -m hydms.pipeline.smoke — the whole chain in 12.1 s (+5 more)

### Community 135 - "044 Screen Interface A"
Cohesion: 0.19
Nodes (13): apply_screens — the protocol is a promise, the runner is the enforcement, Screen a batch, never a candidate at a time (5 ms featurize floor), Screen interface: a verdict with a reason, never a silent drop, _fingerprint: position-weighted content hash catches in-place mutation, INDETERMINATE: a screen that cannot judge rejects (fail-closed), Screen protocol (name, verdict(), declared reason vocabulary), temperature_window() — the worked config-driven screen, an outer bound only, Element Mover's Distance novelty screen (+5 more)

### Community 136 - "Tooling"
Cohesion: 0.15
Nodes (10): pytest_config(), Regression tests for the test tooling itself. These exist because two of the…, Gate HG-1's sentinels are selected by marker; an unregistered marker errors…, Setting `norecursedirs` replaces pytest's defaults rather than extending them.…, If these were ever made safe, the interlock could be relaxed. Until then, it…, No collected module may live outside tests/ — the interlock's observable…, test_collected_tests_come_only_from_this_directory(), test_leak_marker_is_registered() (+2 more)

### Community 137 - "Requirements"
Cohesion: 0.21
Nodes (11): cbfv.composition, Machine_Model Pipeline Guide, boruta (dependency), CBFV (dependency), cleanlab (dependency), Machine_Model Dependency Stack, matminer (dependency), shap (dependency) (+3 more)

### Community 138 - "Readme"
Cohesion: 0.18
Nodes (12): Two Code Trees Invariant (hydms/ vs Machine_Model/src/), Denied Paths, Rewrite Machine_Model/src/ In Place (rejected alternative), Thermodynamics Surrogate (dH, dS, van 't Hoff), Witman et al. 2020 - Empirical Intermetallic Hydride Design Principle, CBFV Featurisation (Magpie + JARVIS), extract_features_cbfv.py, HydMS - Hydrogen Storage Capacity Prediction (README) (+4 more)

### Community 139 - "Comparison"
Cohesion: 0.21
Nodes (6): _markdown(), DataFrame, A GitHub table from a frame, without taking a dependency on ``tabulate``. The…, One row per published feature: how it fared, and what it costs. The table card…, The frames to publish beside the document, by file stem. The evidence travels…, Item 3: the run over the pool the published 22 actually came from. Its two…

### Community 140 - "Comparison"
Cohesion: 0.24
Nodes (3): ``5`` as ``five``, and anything larger as itself., ``name (k/5)`` for the features the whole-split run kept, or the ones it…, _spelled()

### Community 141 - "001 Pin And Lock"
Cohesion: 0.17
Nodes (12): Rebuild blocked by HTTP 403 on the defaults channel, conda env export writes python-graphviz into the pip block, Card #1 — Pin and lock the Project conda environment, One lock file had to become two (conda + pip --no-deps), CBFV is unlicensed and must never become a runtime dependency, GPL-3.0-or-later replaces the MIT licence, Core deps exclude what is not yet installed; uq/search/novelty/app/parity extras, Card #2 — Scaffold the hydms package with pyproject and GPL-3.0 (+4 more)

### Community 142 - "081 App Chart Vocabulary"
Cohesion: 0.18
Nodes (12): Card #81: App chart vocabulary, Domain strip chart, Nearest neighbours chart (k closest by ElMD), A number rendered large and alone reads as certain, Prediction band chart, Temperature sweep chart, The app is an HTTP client of the service, not an in-process caller, app/main.py — the primary user journey (+4 more)

### Community 143 - "Spike Feature Provenance"
Cohesion: 0.24
Nodes (11): build_sample(), columns_for(), load_selected(), main(), DataFrame, Resolve which CBFV element-property table produces each selected feature. Card…, The feature names the published pipeline selected, in SHAP-importance order., Column names CBFV emits for one table, using the original script's exact… (+3 more)

### Community 144 - "Contract"
Cohesion: 0.18
Nodes (9): PredictionRequest, What a caller asks: one composition at one temperature. Deliberately the…, The request as JSON-ready primitives., What a caller would have asked -- the #75 request, built from this probe., `'Pr1Co5 '` and `'Pr1Co5'` are one material and the *pipeline* is what says so.…, Refusing it here would make the screen's verdict unobservable -- what #44…, test_a_request_keeps_the_formula_exactly_as_written(), test_a_temperature_outside_the_trained_range_is_a_verdict_not_a_construction_error() (+1 more)

### Community 145 - "Scaler"
Cohesion: 0.27
Nodes (7): Any, NoReturn, Always raises. A fitted scaler is a value, and refitting it is the leak., Always raises -- the scikit-learn shortcut, and the one that hides a refit., Always raises. Updating the statistics from candidates is the same defect., ``RobustScaler`` with the percentiles pinned, imported lazily. Deferred so that…, _robust_scaler()

### Community 146 - "Selection"
Cohesion: 0.20
Nodes (6): FoldSelection, One selection per outer fold, and what the folds agree about. There is…, Features every fold selected, in the first fold's order. The conservative…, Every feature any fold selected, in first-seen order. The permissive reading., Fold by fold: rows fitted on, rows removed, features selected, and which. The…, How many folds selected each feature, most agreed-upon first. The number that…

### Community 147 - "023 Scaler Fit Once"
Cohesion: 0.18
Nodes (11): FittedScaler — a transform-only wrapper with no fit, The persisted scaler has lost its named consumer (open), Persist the result, not the estimator, MultiQuantile:alpha=0.1,0.5,0.9 — the interval-emitting head, The artifact stores the correction as a number, not a pickled MAPIE object, Raw quantile heads cover 64.4% against a nominal 80%, lcb is a first-class output so no caller can rank on the mean, The model consumes raw, unscaled features (+3 more)

### Community 148 - "071 Gate Hg 1"
Cohesion: 0.18
Nodes (11): CONTEXT.md domain glossary, CONTEXT.md — 26 terms in nine groups, Inclusion rule: a term is in only if conflating it already cost something, Three R² values need three names: procedure, artifact, transfer, A gate that cannot go red is not a gate, GATE HG-1: leak sentinels, one test per named leak, hydms/qa/detectors.py — detectors separated from subjects, The card's L9 wording conflates two properties of a keyed merge (+3 more)

### Community 149 - "074 Metamorphic For Featurize"
Cohesion: 0.20
Nodes (11): Cross-check every formula with hydms.data.load.parse_formula, _dictify drops unknown symbols and keeps the rest — silent partial parse, A fixed guard kept its old reason: the refusal misnamed the mechanism, QA protocol: what must be tested at each layer, Four test kinds: golden, metamorphic, contract, sentinel, docs/QA-PROTOCOL.md — the per-layer testing contract, Metamorphic tests for featurize() and predict(), Case is a refusal: Co is cobalt, CO is carbon and oxygen (+3 more)

### Community 150 - "Context"
Cohesion: 0.22
Nodes (10): Alloy Family, Artifact Score, Procedure Score, Transfer Score, HydMS Vocabulary Glossary (CONTEXT.md), Beltrame et al. 2025 - ML and Data Augmentation for Metal Hydrides, Durdy et al. 2022 - Kernelised Leave One Cluster Out CV, Leave-One-Alloy-Class-Out Cross-Validation (+2 more)

### Community 151 - "Benchmarks"
Cohesion: 0.22
Nodes (10): Architecture A — enumeration over a grid, Architecture B — NSGA-II population search, Featurisation throughput (BENCHMARKS.md), hydms.descriptors.benchmark, require_self_consistent — 5 ms of per-call composite auditing, PRD risk R6 — batched featurisation, no per-candidate loops, The enforced floor: 1,000 formulae/s at batch 10,000, pymoo — NSGA-II on the composition simplex (+2 more)

### Community 152 - "Hg2 Refusal Path"
Cohesion: 0.20
Nodes (10): Enum, _not_always(), How a declared code stands at the request door, where it is not simply…, Built in a function so the codes are imported rather than spelled. See…, Reachability, str, Card #76's finding, as a standing assertion rather than a paragraph., The `untrusted-family` failure, staged on a code this fit really does reach. (+2 more)

### Community 153 - "Validation"
Cohesion: 0.20
Nodes (6): FoldSpace, The numbering that makes two folds *the same fold* when they hold out the same…, The id of the fold holding out exactly these keys, issuing one if it is new., The id already issued for these keys, or ``None``. Never issues one. The read-…, test_an_unseen_fold_has_no_id_and_asking_does_not_issue_one(), test_two_folds_over_the_same_materials_share_an_id()

### Community 154 - "009 Raw Loaders With"
Cohesion: 0.22
Nodes (10): Open: whether a declared correction layer sits above the loader, The dataset uses 55 elements, not the 54 REPORT.md states, The HyStor spreadsheet has no loader (openpyxl absent, not a fourth source), The loader normalises nothing — whitespace and malformed formulae pass through, Schema bounds ask 'is this a temperature at all?', not 'is it in range?', Card #9 — Raw loaders with schema validation, log1p / expm1 as the only two transform entry points, A named Series carries its space; log_log_ cannot be produced (+2 more)

### Community 155 - "088 Group Aware Nested"
Cohesion: 0.22
Nodes (10): Parity plot with the LOACO version at the same scale, Card #88: Group-aware nested cross-validation protocol, A fold id is issued for content, not by counting, Leak L4: the same splits object tunes and then reports, tuned_on is measured, not declared, Leak L6: selection fitted over the rows its score was computed on, LOCO R² 0.2734 against random-split 0.7459, Macro versus support-weighted average (+2 more)

### Community 156 - "Predict"
Cohesion: 0.22
Nodes (7): AssertionError, DataFrame, _ExplodingScaler, DataFrame, A stored scaler that refuses to be used. The whole of the "never applied"…, An artifact directory holding two promoted-quality versions of the same model.…, store()

### Community 157 - "Screening"
Cohesion: 0.25
Nodes (8): LabelIssues, CleanLab's verdict on a set of rows, in the two columns :func:`screen` accepts.…, How many rows were flagged., MonkeyPatch, The bypass, closed: the rows the stages fit on are the rows screening left.…, Screening is handed the fold's rows, which is why it may drop any of them. The…, test_screening_inside_the_selector_cannot_reach_a_row_it_was_not_given(), test_selection_consumes_the_screening_verdict()

### Community 158 - "Evaluate"
Cohesion: 0.22
Nodes (9): Any, ``resamples`` arrays of positional row indices, drawn with replacement. **The…, _replicates(), 83 of the 780 real training groups span more than one temperature. So a group…, Q6: one resample, every breakdown computed from it — and it is shared by…, The property, at its sharpest: one material, and the group bootstrap has no…, test_a_group_resample_draws_whole_compositions_and_a_row_resample_does_not(), test_a_resampled_group_carries_all_of_its_rows() (+1 more)

### Community 159 - "Selection"
Cohesion: 0.22
Nodes (5): The chosen features, and every count behind them. Attributes: features: The…, How many features were selected., The counts and the chosen names as one row of a table of selections. Defined…, Stage by stage: in, out, dropped, restored -- the counts the card asks be…, Selection

### Community 160 - "012 Re Join Alloy"
Cohesion: 0.28
Nodes (9): Missing keys raise as loudly as unknown ones, Alloy_class validated against a closed set of ten, The unwired sentinel turns HG-1 red before a wrong line is written, AC-6 feasible counted in compositions: smallest class A2B with 24 of 1115, L13 sentinel — assert_metadata_survives over the real featurisation path, Leak L8 — joining on the raw formula string re-imports the collision, A row with a missing class refuses; there is no UNKNOWN, Card #12 — Re-join Alloy_class on the canonical key (+1 more)

### Community 161 - "010 Keyed Merge Replacing"
Cohesion: 0.25
Nodes (9): (Composition, temperature(K)) is not unique: 1279 rows, 1272 pairs, merge_datasets.py:49 keeps the first of two identically-named columns, Card #10 — Keyed merge replacing the positional concat, Leak L9 — positional pd.concat(axis=1) with no join key, hydms.data.merge.merge_features, The spine's index label is the row identity, Compute the log target, never join it from hydride_prefeaturizing.csv, temperature(K) arrives twice in the concat — a third disguise of merge_datasets.py:49 (+1 more)

### Community 162 - "Context"
Cohesion: 0.25
Nodes (8): Blocker (blocked_by dependency graph), Stage (S0-S8, Phase H execution order), User Story (S1-S12, PRD section 5), scripts/check_board.py, scripts/check_freeze.py, User Stories S1-S12, The Coverage Floor Is Unenforceable Today (card #86), Definition of Done

### Community 163 - "Canonical"
Cohesion: 0.25
Nodes (5): Collapse, CollapseStage, One normalisation step and what it merged. Attributes: name: ``"raw"``,…, The accounting of 1149 formula strings down to 1115 compositions. Reported per…, Account for the collapse from formula strings to compositions, step by step. On…

### Community 164 - "Metadata"
Cohesion: 0.25
Nodes (8): class_distribution(), DataFrame, What reconciliation did to each class, in rows and in compositions. The…, Counted in compositions, because #88's folds group on the canonical key. The…, Class by class, not as a total. Measured during card #12; a change here is a…, test_leave_one_class_out_has_ten_non_trivial_folds(), test_the_distribution_is_reported_in_precedence_order(), test_the_distribution_moves_into_the_structural_families()

### Community 165 - "Refusals"
Cohesion: 0.29
Nodes (8): The one code and the one sentence a caller receives, from every screen that…, resolve(), Run order is the only precedence declared across screens, so it is the tiebreak., Admitted *because* the rules did not run is the silent drop's mirror image. A…, test_resolve_carries_every_screens_sentence_when_nothing_rejected(), test_resolve_refuses_a_candidate_no_screen_judged(), test_resolve_takes_the_first_rejecting_screens_code_and_every_reason(), _verdict()

### Community 166 - "008 Provenance Spike Resolve"
Cohesion: 0.25
Nodes (8): extract_features_cbfv.py:31 passes elem_prop='magpie' and reproduces nothing, Statistic-of-composite versus composite-of-statistic (risk R3), unresolved, The 22 features split 15 oliynyk / 6 jarvis / 1 temperature passthrough, Card #8 — PROVENANCE SPIKE: resolve elem_prop for all 22 features, Run the real featuriser rather than diffing table headers, CBFV.composition.parse_formula validates nothing, The Gordy hole — the 22-feature contract refuses 266 of 1279 curated rows, Two hard gates: #8 provenance spike and #21 featuriser parity

### Community 167 - "Metadata"
Cohesion: 0.25
Nodes (8): curated(), matrix(), DataFrame, Three rows shaped like `with_metadata`'s output, on a non-trivial index. The…, What a featuriser returns: float64 features on the caller's own labels., The curated dataset, loaded once. Read-only: nothing here mutates it., record(), resolved()

### Community 168 - "Protocol"
Cohesion: 0.29
Nodes (4): candidates(), Any, DataFrame, Four candidates, labelled, so a dropped or reordered row is visible by name.

### Community 169 - "Prd Inverse Design"
Cohesion: 0.33
Nodes (7): Caveat on the Three ML Skills, Task Router (task to document to skill), Leak (a named, sited influence of held-out data), CBFV Licence Problem, Code Audit Findings (2026-08-30), Three Validation Leaks (test-set early stopping, pre-CV selection, model choice on test), Held-Out Data Is Read Once, at the End

### Community 170 - "Novelty"
Cohesion: 0.29
Nodes (7): main(), _number(), TextIO, A distance as it should read in a sentence: 11.732, not 11.731999999999999., ``--emit`` rewrites the committed reference; no argument prints what it holds., CaptureFixture, test_main_prints_what_the_reference_holds()

### Community 171 - "Readme"
Cohesion: 0.29
Nodes (7): Twelve layer subpackages derived from the cards, HydMS Inverse Design Board (frozen), Tickets cut by layer, not by phase, The eight layers L0–L7, The evaluator is the deep module; Search is a seam, The five phases P0, P1, PT, PA, PB, Phase 1 has two halves: code (9–34) and prose (37)

### Community 172 - "076 Predict Capacity Over"
Cohesion: 0.33
Nodes (7): domain-reference.json — generated beside the module by --emit, ratio_vector is not reproducible across processes (set-order hashing), novelty-reference.json — 780 compositions, ceiling 11.7320, ArtifactBundle — a version plus the screens and their references, _check_columns — the bundle is the only place screens and _candidate can be made to agree, reference_digests — digested, not pinned (fit-time binding owed by #91), The service refuses to start if no artifact version is resolvable

### Community 173 - "Inverse Design Methods"
Cohesion: 0.29
Nodes (7): CatBoost (dependency), Angelopoulos & Bates 2023 - Conformal Prediction, CatBoost Native Uncertainty, Conformal Prediction Intervals, Lower-Confidence-Bound Ranking, MAPIE, Uncertainty Quantification Guard Rail

### Community 174 - "Report"
Cohesion: 0.29
Nodes (7): Optuna (dependency), optuna_objective(), optimize_catboost(), objective(), Optuna Hyperparameter Optimisation, Akiba et al. 2019 - Optuna, Optuna NSGA-II/III Samplers

### Community 175 - "Novelty"
Cohesion: 0.29
Nodes (5): An ElMD stand-in that reads exactly the composition it is given. The two…, Neither reading can be trusted, so the reason names both rather than picking…, _Reads, test_a_formula_elmd_reads_as_nothing_is_refused_in_those_words(), test_two_parsers_that_name_different_elements_refuse_and_say_so()

### Community 176 - "Qa Protocol"
Cohesion: 0.33
Nodes (6): Gate (an acceptance criterion executed, not remembered), A Gate Must Be Able to Fail, The Reason Must Travel With the Refusal, Reviewer Checklist, How to Read a Change to This File (four kinds of diff), A Sentence That Only Echoes the Formula Does Not Count As Naming

### Community 177 - "Canonical"
Cohesion: 0.33
Nodes (4): _fractions(), How close the key came to merging two materials that are not the same one.…, Measure how much room the key had, over a whole corpus. Rounding is a decision…, Separation

### Community 178 - "Artifact"
Cohesion: 0.33
Nodes (5): Candidate, Path, The version a gate is scoring, loaded, with the reason it was chosen.…, One clause naming what answered, for the result message., The version under certification, loaded and ready to predict from. Args: cfg:…

### Community 179 - "Loco"
Cohesion: 0.33
Nodes (6): _direction(), Which way the support-weighted mean falls, measured rather than predicted. A…, parametrize, The sentence that got this wrong once is now generated from the two numbers., test_an_undefined_average_is_not_described_as_higher_or_lower(), test_the_document_states_the_direction_it_measured_not_one_it_predicted()

### Community 181 - "Canonical"
Cohesion: 0.20
Nodes (6): Asserted over every formula in both raw files, which is what the card asks for.…, A class outside the order would fail on the row that carried it, not before., Neither file's class set contains the other's, so a re-join needs a stated…, test_canonicalisation_never_silently_merges_two_different_materials(), test_precedence_covers_the_declared_vocabulary_exactly(), test_the_two_class_vocabularies_are_not_nested()

### Community 182 - "Predict"
Cohesion: 0.33
Nodes (6): A real `GateReport`, so this file cannot drift from the shape the harness…, The gate check is never relaxed here. `artifacts.load` takes a…, A model and a manifest from two different runs. The featuriser is driven by the…, report(), test_a_model_fitted_outside_its_own_contract_is_refused(), test_a_version_whose_gates_are_not_established_cannot_predict()

### Community 183 - "Scaler"
Cohesion: 0.33
Nodes (6): Path, A v1 holding the fitted scaler, loaded back with gates deliberately unchecked.…, What a version written before this card holds: something with a `fit` on it., saved(), test_a_bundle_without_a_scaler_names_what_it_does_hold(), test_a_version_holding_a_raw_estimator_is_refused()

### Community 184 - "Ci"
Cohesion: 0.40
Nodes (5): scripts/check_board.py (CI step), scripts/check_freeze.py (CI step), CI job: hygiene (board, freeze, ruff, mypy), Exact lint pins ruff==0.8.4 and mypy==1.13.0, HG-4 — Hygiene gate

### Community 185 - "Hg2 Refusal Path"
Cohesion: 0.40
Nodes (5): fixture, _forget_bundles(), A configuration pointed at one real, cheap, ungated artifact version., The delivery layer caches by ``(store, version)``; every test here writes a new…, served()

### Community 186 - "Scaler"
Cohesion: 0.40
Nodes (3): DataFrame, Scale a batch, by name, in fitting order. The columns must be exactly…, One row per feature: its centre, its scale, and whether its span was zero. For…

### Community 187 - "084 Batch Csv Screening"
Cohesion: 0.40
Nodes (5): A batch must not launder a refusal into a number, Card #84: Batch CSV screening page, "NaN" parses to sodium and nitrogen, Mg0853Ni0.125La0.022: a missing decimal point that parses cleanly, A right verdict with a false reason

### Community 188 - "Context"
Cohesion: 0.50
Nodes (4): Capacity (maximum material gravimetric wt%), System Capacity, Usable Capacity, No System-Level Claim (material vs system capacity)

### Community 190 - "Ac3 Conformal Coverage"
Cohesion: 0.50
Nodes (4): _coverage(), ndarray, Series, The share of observations the band contains, inclusive at both ends.

### Community 192 - "Comparison"
Cohesion: 0.50
Nodes (3): Re-wrap the prose paragraphs of a generated document, leaving structure alone.…, The published write-up, every number in it read from the tables above. Reflowed…, _reflow()

### Community 193 - "030 Leave One Alloy"
Cohesion: 0.50
Nodes (4): Estimability is a property of R2, not a taste, AC-6's gate reads the committed tables rather than refitting, The LOCO run: ten class folds, 4 h 07 m, committed tables, Untracked probe tables cited by value in three committed documents

### Community 194 - "Verify Environment"
Cohesion: 0.67
Nodes (3): main(), Prove the pinned environment can actually be rebuilt from the files in this…, run()

### Community 195 - "Hg2 Refusal Path"
Cohesion: 0.50
Nodes (4): A prediction path that answers with a number and nothing else., No probe set can establish this. Reading every exit can, and that is the…, _returns_a_float(), test_a_branch_returning_a_bare_number_is_caught_by_reading_the_source()

### Community 196 - "Context"
Cohesion: 0.67
Nodes (3): hydms.data.canonical.group_keys, Canonical Composition, Formula (source composition string)

### Community 197 - "Context"
Cohesion: 0.67
Nodes (3): Probe (reduced-budget number, never a result), Smoke Run (chain check vs cost check), The Stated Inputs (probe baseline table)

### Community 198 - "Ac3 Conformal Coverage"
Cohesion: 0.67
Nodes (3): DataFrame, The same model's heads in weight percent with **no** correction applied.…, _raw_heads()

### Community 199 - "Ac6 Leave One Class"
Cohesion: 0.67
Nodes (3): Path, One CSV as rows of strings, using the stdlib. ``csv`` rather than pandas on…, _read()

### Community 201 - "Predict"
Cohesion: 0.67
Nodes (3): PredictionError, ValueError, The surrogate cannot answer, and the reason is the artifact rather than the…

### Community 202 - "015 Data Layer Golden"
Cohesion: 0.67
Nodes (3): The 1,115-vs-1,114 off-by-one is Eu1Ni5, Eu1Ni5 (row 516) — a corrupted published feature row, No europium-containing formula may be compared at all

### Community 203 - "029 Evaluation Metrics With"
Cohesion: 0.67
Nodes (3): Screening removes 2%-20% of a fold's training rows, The bootstrap resamples out-of-fold predictions, not five fold scores, Risk R4: nested R2 0.746 wt% against REPORT.md's published 0.892

### Community 204 - "Report"
Cohesion: 0.67
Nodes (3): manage_outliers(), CleanLab Label-Quality Screening, Northcutt et al. 2021 - Confident Learning

### Community 205 - "Canonical"
Cohesion: 0.67
Nodes (3): MonkeyPatch, `docs/QA-PROTOCOL.md` section 5: the measurement is shown red on purpose. At…, test_three_significant_digits_would_merge_two_materials()

### Community 206 - "Loco"
Cohesion: 0.67
Nodes (3): Path, Half a document is worse than none: it would publish an average with no per-…, test_emit_refuses_a_partial_set_of_tables_and_names_what_is_missing()

## Ambiguous Edges - Review These
- `Models Evaluated Table` → `13-Model Regression Benchmark`  [AMBIGUOUS]
  Machine_Model/README.md · relation: references

## Knowledge Gaps
- **201 isolated node(s):** `Akiba et al. 2019 - Optuna`, `Angelopoulos & Bates 2023 - Conformal Prediction`, `Baird et al. 2022 - DiSCoVeR`, `Choudhary et al. 2020 - JARVIS`, `Dan et al. 2020 - MatGAN` (+196 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Models Evaluated Table` and `13-Model Regression Benchmark`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `load()` connect `Config` to `Featuriser Element Tables`, `Delivery Refusal Vocabulary`, `Leak Sentinels`, `Canonical Composition Key`, `Predict`, `Keyed Feature Merge`, `External Libraries and Archival Report`, `Element Mover's Distance Novelty`, `Descriptor Feature Contract`, `Smoke Pipeline Fixture`, `Screen Protocol Runner`, `Delivery Contract Types`, `Leak Inventory`, `Descriptor Computability`, `Conformal Calibration`, `Surrogate Training Run`, `Calibrated Quantile Heads`, `Artifact Store Promotion`, `Grouped Data Splits`, `Gate CLI Reporting`, `Target`, `Applicability`, `Benchmark`, `Harness`, `Evaluate`, `Metadata`, `Window`, `Model`, `Promote`, `Metadata`, `Comparison`, `Store`, `Validation`, `Deploy`, `Domain`, `Selection`, `Novelty`, `Validation`, `Conftest`, `L13 Class Survival`, `Evaluate`, `Evaluate`, `Ac2 Parity`, `Metadata`, `Loco`, `Init`, `Ac1 Reproducibility`, `Cli`, `Novelty`, `Novelty`, `Loco`, `Loco`, `Evaluate`, `Evaluate`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `Optimise in Composition Space (Option A)` connect `Report` to `Inverse Design Methods`, `Requirements`, `Readme`, `Prd Inverse Design`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `Architecture A - Screen-and-Rank` connect `Prd Inverse Design` to `Refusals`, `077 Gate Hg 2`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `featurize()` (e.g. with `PropertyTable` and `Statistics`) actually correct?**
  _`featurize()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 49 inferred relationships involving `ScreenError` (e.g. with `ApplicabilityDomain` and `DomainReference`) actually correct?**
  _`ScreenError` has 49 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Akiba et al. 2019 - Optuna`, `Angelopoulos & Bates 2023 - Conformal Prediction`, `Baird et al. 2022 - DiSCoVeR` to the rest of the system?**
  _201 weakly-connected nodes found - possible documentation gaps or missing edges._