# VSPillars

Supplementary evaluation settings and archived numerical results for **VSPillars: Fourier-Based Height-Distribution Encoding for Aerial LiDAR 3D Detection**, by Jiajun Shen and Jun Tao, Department of Aeronautics and Astronautics, Fudan University.

This release supports the ICAUAS 2026 manuscript. It provides the class-dependent evaluation thresholds, individual-run results, complete class-wise comparisons and timing details that can be referenced from a compact paper. All measurements come from existing evaluations; this release adds no new training, inference or deduplicated evaluation.

## Contents

| File | Contents |
| --- | --- |
| [Evaluation protocol](docs/evaluation_protocol.md) | Split, AP matching, adapted NDS and all 22 categories' thresholds |
| [Experiment details and results](docs/experiment_details.md) | Comparison conditions, paired results, complete class-wise table and latency scope |
| [Evaluation configuration](configs/wisar3d_evaluation.json) | Exact evaluator configuration shared by the 17 archived accuracy evaluations |
| [Accuracy results](results/accuracy_runs.json) | Unrounded metrics, per-threshold and per-class AP, recall, and checkpoint hashes |
| [Class-wise results](results/classwise_ap.json) | Three-seed means and individual paired differences for all 22 classes |
| [Timing results](results/latency_runs.json) | Four runs, including 20 warm-up and 200 measured forward-pass durations per run |
| [Provenance](provenance.json) | Original archive hashes, baseline manuscript hash and extraction policy |

## Check the reported arithmetic

From the repository root, run Python 3.9 or later:

```sh
python scripts/verify_supplement.py
```

The script uses only the Python standard library. It verifies per-threshold AP aggregation, macro mAP, adapted NDS, paired means and sample standard deviations, all class-wise differences, and timing means and interpolated P95 values. It also checks the numerical values against those reported in the baseline manuscript.

This is a consistency check of archived numerical summaries, **not a detector evaluation script**. It does not rerun inference, recompute AP from predictions or reproduce model training. No dataset, annotations, prediction caches, weights or full detector implementation are redistributed here.

## Interpretation

The primary comparison uses paired seeds 666, 2026 and 4242, evaluated at epoch 80 on all 1,261 frames of the official WiSAR3D validation split. The split was also used during development. The additional PointPillars comparison uses the same dataset and is not an independent-dataset test. The alternative descriptors differ in their input information and architecture; their scores do not isolate an advantage of Fourier bases alone.

The original local archive hashes identify the inputs used to prepare this supplement. Those original files are not distributed, so the hashes are provenance identifiers rather than proof of publicly available training artifacts. All publicly included metrics are available in the JSON files above.

For a stable manuscript reference, use the GitHub permalink for the specific commit of this supplement instead of relying only on the moving `main` branch.
