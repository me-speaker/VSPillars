# WiSAR3D evaluation protocol

## Dataset and checkpoint selection

All accuracy records in this release use the official WiSAR3D validation split of 1,261 frames and 22 categories. The training split contains 1,372 frames. Every reported accuracy checkpoint is from epoch 80. No deduplicated subset or second dataset is evaluated in this release.

The machine-readable [configuration](../configs/wisar3d_evaluation.json) is copied from the archived evaluator configuration. It is identical across all 17 accuracy records included here; it is not a newly selected evaluation protocol. Underscores in class identifiers correspond to spaces in the paper.

## AP and adapted NDS

Matching uses horizontal center distance, `sqrt((x_pred - x_gt)^2 + (y_pred - y_gt)^2)`, in meters. For each class, AP is computed at its three distance thresholds and averaged. mAP is the unweighted mean of those 22 class AP values. The configuration sets minimum recall and precision to 0.1, with at most 500 predicted boxes per sample.

True-positive translation, scale and orientation errors use the middle distance threshold for each class. The adapted detection score is

```text
NDS = (3 * mAP + max(0, 1 - mATE)
               + max(0, 1 - mASE)
               + max(0, 1 - mAOE)) / 6
```

Here `mATE`, `mASE` and `mAOE` are the evaluator's aggregated translation, scale and orientation errors. This WiSAR3D adaptation has no velocity or attribute terms and is not the standard nuScenes NDS. Translation matching uses XY distance; scale error depends on 3D box dimensions. These aggregate scores do not isolate center-height or box-height accuracy.

The JSON excerpts retain the already-aggregated TP errors. The verification script checks NDS from those errors; it does not reconstruct TP matching or AP curves from raw predictions. The separately included class-agnostic 3D IoU recall is a complementary overlap statistic, not an alternative definition of AP.

## Class dependent thresholds

The following table is generated from the same configuration JSON. `d2` is also the TP-error matching threshold.

| Category | d1 (m) | d2 (m) | d3 (m) |
| --- | ---: | ---: | ---: |
| Vehicle | 0.19 | 0.95 | 1.72 |
| Mattress | 0.08 | 0.38 | 0.69 |
| Ball | 0.03 | 0.13 | 0.23 |
| Gazebo | 0.29 | 1.44 | 2.59 |
| Canopy | 0.32 | 1.60 | 2.88 |
| Chair | 0.05 | 0.24 | 0.43 |
| Small table | 0.06 | 0.29 | 0.52 |
| Big table | 0.08 | 0.41 | 0.73 |
| Tripod pipe | 0.06 | 0.29 | 0.52 |
| Barrel | 0.05 | 0.26 | 0.47 |
| Tent | 0.21 | 1.07 | 1.92 |
| Box | 0.05 | 0.23 | 0.41 |
| Drone case | 0.07 | 0.36 | 0.64 |
| Small bin | 0.03 | 0.16 | 0.29 |
| Ramp | 0.07 | 0.34 | 0.62 |
| Sitting person | 0.06 | 0.31 | 0.57 |
| Standing person | 0.05 | 0.25 | 0.45 |
| Cone | 0.01 | 0.06 | 0.11 |
| Flag | 0.06 | 0.31 | 0.56 |
| Pipe | 0.02 | 0.10 | 0.17 |
| Porta potty | 0.11 | 0.57 | 1.02 |
| Play tunnel | 0.03 | 0.17 | 0.30 |

## Preprocessing and prediction filtering

The detector consumes `(x, y, z, r)`, with raw intensity divided by `2^16` to obtain `r`. The dynamic PillarNet path crops points in XY and does not apply a hard Z cutoff or a per-pillar point cap. Training GT box centers are filtered using the configured 3D range; validation uses the released annotations without that training-time filter.

For the explicit descriptor only, height is normalized using the fixed interval `[-2, 4]` meters and clipped to `[0, 1]`; intensity is also clipped to `[0, 1]`. The PFN still uses the original input Z and scaled intensity values. Clipping the descriptor is not removal of those points from the PFN.

The primary detector's prediction filtering uses the configured 3D center range, score threshold 0.1, NMS threshold 0.1 and a limit of 500 boxes. These inference settings are distinct from the evaluator's category-dependent AP thresholds. The second detector configuration has its own spatial range, documented in [experiment details](experiment_details.md).

## Scope and provenance

The baseline manuscript reports byte-identical point-cloud pairs within validation. All results released here retain the complete official validation list; no deduplication sensitivity result is claimed. Repeated seeds assess run-to-run variation under this configuration, not independent-scene generalization.

See [provenance.json](../provenance.json) for source archive and checkpoint hashes. Dataset files, raw predictions and the evaluator implementation are not included. The configuration and summaries preserve the settings and numerical evidence used in the paper but are not a complete executable reproduction package.
