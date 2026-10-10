# Experiment details and archived results

## Main PillarNet configuration

The primary setup uses horizontal pillars of 0.075 m, a 2048 by 2048 grid and output stride 8 (0.6 m output cells). The configured ranges are X [-40.88, 112.72], Y [-74.88, 78.72] and Z [-2, 4], in meters. Point, GT and prediction filtering are stage-specific as described in the [evaluation protocol](evaluation_protocol.md).

Training uses 80 epochs in FP32, eight GPUs and two frames per GPU (global batch size 16). The optimizer is Adam with a one-cycle schedule, learning rate 0.003, weight decay 0.01 and gradient-norm clipping at 10. Shared augmentations comprise training-set GT database sampling (excluding entries with fewer than five points), X-axis world flipping, Z-axis rotation within [-pi/4, pi/4] and global scaling in [0.95, 1.05].

P0 is the retained dynamic PillarNet baseline. P1 adds twelve height Fourier moments (K = 6) and five statistics: log(1 + point count), normalized-height mean and population standard deviation, and clipped-intensity mean and population standard deviation. Its projection is 17 -> 32 -> 32; concatenation with the 32-D PFN feature is followed by 64 -> 32 fusion. The downstream detector is unchanged. P1-S and P1-F retain only the five statistics and twelve Fourier moments, respectively.

The archived launch commands specify no external pretrained checkpoint. Available records do not establish the complete initialization history of every paired run, so the main comparison is not relabeled as uniformly verified training from scratch.

## Three paired seeds

The primary comparison uses seeds 666, 2026 and 4242, with one P0/P1 pair per seed. Values below are mean +/- **sample** standard deviation (denominator n - 1). All AP and NDS scores use the 0 to 1 scale.

| Model | mAP | NDS |
| --- | ---: | ---: |
| P0 | 0.6289 +/- 0.0094 | 0.7136 +/- 0.0060 |
| P1 | 0.6848 +/- 0.0028 | 0.7609 +/- 0.0034 |

Mean improvements computed before rounding are 5.59 mAP and 4.73 NDS percentage points. All three pairs improve in both metrics. Individual unrounded results, per-threshold AP and checkpoint identities are retained in [accuracy_runs.json](../results/accuracy_runs.json).

## Component and descriptor comparisons

Each row below is one archived run, not a three-seed mean. The default P1 seed-2026 row also serves as K = 6 in the frequency sweep.

| Run | Fourier K | mAP | NDS |
| --- | ---: | ---: | ---: |
| P0_seed2026 | -- | 0.6220 | 0.7097 |
| P1_seed2026 | 6 | 0.6852 | 0.7604 |
| P1S_seed2026 | -- | 0.6710 | 0.7459 |
| P1F_seed2026 | 6 | 0.6805 | 0.7574 |
| RBF_seed2026 | -- | 0.6751 | 0.7512 |
| SoftHist_seed2026 | -- | 0.6836 | 0.7608 |
| SoftHist_seed4242 | -- | 0.6803 | 0.7604 |
| PillarHist_seed2026 | -- | 0.6657 | 0.7499 |
| P1_K2_seed2026 | 2 | 0.6861 | 0.7592 |
| P1_K4_seed2026 | 4 | 0.6861 | 0.7629 |
| P1_K8_seed2026 | 8 | 0.6861 | 0.7613 |
| D0 | -- | 0.3298 | 0.4833 |
| D1 | 6 | 0.3980 | 0.5343 |

P1-S, P1-F and P1 differ in descriptor content and projection input width. Each adds projection/fusion capacity relative to P0; these comparisons do not isolate a basis-only effect.

RBF and Soft-Hist retain the PFN and average 17 height-only basis responses, without the five basic statistics. Centers are evenly spaced in [0, 1]. RBF responses are exp(-(u-c)^2 / (2 sigma^2)), with sigma = 0.12. Soft-Hist responses are exp(-abs(u-c)/tau), normalized over the 17 centers, with tau = 0.08. The seed-2026 Soft-Hist run resumed at epoch 18 and completed 80 epochs; the seed-4242 run was trained from scratch.

The FP32 PillarHist adaptation replaces the original PFN. Its archived evaluation configuration has 64 height bins over [-2, 4] m, with count normalization and XY-center normalization disabled and a 32-D output. This is not the original quantized PillarHist system.

Soft-Hist remains competitive: at seed 2026 it exceeds P1-F in mAP and NDS, while P1 has slightly higher mAP but lower NDS than Soft-Hist. Input information, dimensions and PFN retention differ across candidates, and the limited runs do not establish statistical significance.

The K = 2, 4, 6, 8 sweep uses the joint descriptor, including five statistics, at seed 2026. Its input width is 5 + 2K. Although K = 4 has the highest NDS in this sweep, K = 6 remains the default used in the paired evaluation. The latency runs below are **not** timings for each K value.

## Separate PointPillars configuration

D0 and D1 use the same WiSAR3D validation split, not a second dataset. Each was trained once from scratch for 80 epochs without resuming, with eight GPUs, one frame per GPU (global batch size 8) and automatic mixed precision. Seed values are left unspecified in this public excerpt rather than inferred from unrelated run labels.

This setup uses 0.32 m horizontal pillars, at most 20 points per hard voxel and ranges X [-40.88, 108.88], Y [-74.88, 74.88] and Z [-2, 4] m. D1 is a height-only Fourier augmentation with K = 6 and a 16-channel hidden projection, not the complete P1 descriptor. Its within-configuration gains are 6.83 mAP and 5.10 NDS percentage points; absolute scores should not be ranked against the differently configured PillarNet experiments.

## Full class wise comparison

AP values are averaged over the three paired seeds. Delta is P1 minus P0, computed before rounding; a displayed difference can therefore differ slightly from subtraction of the displayed means.

| Category | P0 mean AP | P1 mean AP | Delta AP |
| --- | ---: | ---: | ---: |
| Vehicle | 0.9203 | 0.9234 | +0.0031 |
| Mattress | 0.8717 | 0.8767 | +0.0050 |
| Ball | 0.5487 | 0.5797 | +0.0310 |
| Gazebo | 0.9619 | 0.9556 | -0.0063 |
| Canopy | 0.9245 | 0.9258 | +0.0012 |
| Chair | 0.6479 | 0.7342 | +0.0864 |
| Small table | 0.5064 | 0.8293 | +0.3228 |
| Big table | 0.6321 | 0.6608 | +0.0287 |
| Tripod pipe | 0.6902 | 0.7524 | +0.0622 |
| Barrel | 0.6194 | 0.7438 | +0.1244 |
| Tent | 0.9212 | 0.9183 | -0.0029 |
| Box | 0.6955 | 0.7647 | +0.0693 |
| Drone case | 0.7244 | 0.7654 | +0.0410 |
| Small bin | 0.5549 | 0.6303 | +0.0754 |
| Ramp | 0.7738 | 0.8203 | +0.0465 |
| Sitting person | 0.1977 | 0.3550 | +0.1573 |
| Standing person | 0.4839 | 0.5266 | +0.0428 |
| Cone | 0.1979 | 0.2905 | +0.0926 |
| Flag | 0.4478 | 0.4098 | -0.0380 |
| Pipe | 0.4269 | 0.4841 | +0.0572 |
| Porta potty | 0.4705 | 0.4655 | -0.0051 |
| Play tunnel | 0.6190 | 0.6541 | +0.0351 |

Mean AP improves in 18 of 22 classes; 15 improve in every pair. Gazebo, Tent, Flag and Porta potty have lower mean AP. Flag and Gazebo decline in all three pairs. The largest decline is Flag (-0.0380). The three largest positive contributions (Small table, Sitting person and Barrel) account for approximately 49.2% of the net sum of class-AP changes. Gains are therefore uneven across classes.

## Evaluation forward pass timing

Timing uses an NVIDIA GeForce RTX 4090, FP32, batch size 1, no test-time augmentation, 20 warm-up frames and 200 measured frames with CUDA synchronization. Each timed forward pass includes VFE, backbone, detection head, post-processing and GT-recall bookkeeping. It excludes data loading, CPU-to-GPU transfer and dataset-level AP/NDS computation.

| Run | Mean (ms) | P95 (ms) | Peak allocated (MB) |
| --- | ---: | ---: | ---: |
| P0_seed666 | 63.11 | 87.75 | 1810.6 |
| P1S_seed2026 | 66.67 | 85.56 | 1811.0 |
| P1F_seed2026 | 69.17 | 98.33 | 1810.6 |
| P1_seed666 | 69.88 | 96.09 | 1811.0 |

The P0/P1 timing pair uses seed 666; the statistics-only and Fourier-only timings use seed 2026. P1 adds 6.77 ms (10.7%) to mean latency, computed before rounding. These are detector-level timings, not isolated encoder timings or demonstrated onboard real-time performance.

Peak allocated CUDA memory is the PyTorch measurement over the full loop including warm-up, reported in the archive's decimal MB units. P95 is linearly interpolated at position 0.95 * (n - 1) in the sorted measured durations. [latency_runs.json](../results/latency_runs.json) includes each forward-pass duration so the mean and P95 can be independently recomputed.

## Evidence boundary

This supplement reorganizes existing measurements. It does not add an independent test set, deduplicated evaluation, formal nuScenes results or deployment tests. The full validation split was also used during development. Numerical consistency can be checked with the included script; complete historical training and raw-prediction evaluation cannot be reproduced from these files alone.
