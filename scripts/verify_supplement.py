"""Verify archived numeric summaries, not inference or raw-prediction evaluation.

Run with Python >= 3.9. No third-party packages, network, GPU or file writes.
"""

import json
import math
from pathlib import Path
import re
from statistics import mean, stdev


ROOT = Path(__file__).resolve().parents[1]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def load(relative):
    def reject_constant(value):
        raise ValueError("Non-standard JSON constant: " + value)

    return json.loads((ROOT / relative).read_text(encoding="utf-8"),
                      parse_constant=reject_constant)


def close(actual, expected, label, tolerance=1e-10):
    check(math.isfinite(actual) and math.isfinite(expected), label + ": finite")
    check(math.isclose(actual, expected, rel_tol=0, abs_tol=tolerance),
          f"{label}: {actual} != {expected}")


def verify():
    config = load("configs/wisar3d_evaluation.json")
    accuracy = load("results/accuracy_runs.json")["runs"]
    latency = load("results/latency_runs.json")["runs"]
    classwise = load("results/classwise_ap.json")
    provenance = load("provenance.json")
    categories = list(config["dist_ths"])
    check(len(categories) == 22, "22 evaluation categories")
    check(config["dist_fcn"] == "center_distance", "XY distance configuration")
    check(config["mean_ap_weight"] == 3, "adapted NDS weight")
    check(config["min_recall"] == config["min_precision"] == 0.1,
          "minimum recall/precision")
    check(config["max_boxes_per_sample"] == 500, "box limit")
    check(set(config["dist_th_tp"]) == set(categories), "TP threshold categories")
    for category, thresholds in config["dist_ths"].items():
        check(len(thresholds) == 3 and 0 < thresholds[0] < thresholds[1] < thresholds[2],
              category + ": three ordered positive thresholds")
        check(config["dist_th_tp"][category] == thresholds[1], category + ": TP threshold")

    by_id = {run["id"]: run for run in accuracy}
    check(len(accuracy) == len(by_id) == 17, "17 unique accuracy runs")
    sources = {source["id"]: source for source in provenance["sources"]}
    expected_source_ids = set(by_id) | {"latency_" + run["run_id"] for run in latency}
    check(len(sources) == len(provenance["sources"]) == 21, "21 unique source records")
    check(set(sources) == expected_source_ids, "source record coverage")
    for source in sources.values():
        for key in ("archive_sha256", "checkpoint_sha256"):
            check(re.fullmatch(r"[0-9a-f]{64}", source[key]) is not None,
                  source["id"] + ": " + key)

    for run in accuracy:
        name = run["id"]
        check(run["epoch"] == 80 and run["num_samples"] == 1261, name + ": epoch/split")
        check(run["checkpoint_sha256"] == sources[name]["checkpoint_sha256"],
              name + ": checkpoint provenance")
        check(set(run["per_class_AP"]) == set(categories), name + ": class AP coverage")
        check(set(run["AP_by_distance"]) == set(categories), name + ": threshold AP coverage")
        for category in categories:
            values = run["AP_by_distance"][category]
            check(sorted(map(float, values)) == config["dist_ths"][category],
                  name + ": thresholds for " + category)
            check(all(math.isfinite(x) and 0 <= x <= 1 for x in values.values()),
                  name + ": AP range for " + category)
            close(mean(values.values()), run["per_class_AP"][category],
                  name + ": class AP " + category)
        close(mean(run["per_class_AP"].values()), run["mAP"], name + ": mAP")
        check(set(run["tp_errors"]) == {"trans_err", "scale_err", "orient_err"},
              name + ": three TP errors")
        check(all(math.isfinite(x) and x >= 0 for x in run["tp_errors"].values()),
              name + ": TP error range")
        nds = (3 * run["mAP"] + sum(max(0, 1 - e) for e in run["tp_errors"].values())) / 6
        close(nds, run["NDS"], name + ": NDS")
        check(all(math.isfinite(x) and 0 <= x <= 1 for x in run["recall_3d_iou"].values()),
              name + ": recall range")

    seeds = [666, 2026, 4242]
    paired = {model: [by_id[f"{model}_seed{seed}"] for seed in seeds]
              for model in ("P0", "P1")}
    for model, runs in paired.items():
        check([r["seed"] for r in runs] == seeds, model + ": seed mapping")
        check(all(r["model"] == model for r in runs), model + ": model mapping")
    expected = {"P0": ("0.6289", "0.0094", "0.7136", "0.0060"),
                "P1": ("0.6848", "0.0028", "0.7609", "0.0034")}
    summary = {}
    for model, runs in paired.items():
        summary[model] = {key: {"mean": mean(r[key] for r in runs),
                               "sample_sd": stdev(r[key] for r in runs)}
                          for key in ("mAP", "NDS")}
        rounded = tuple(f"{summary[model][key][stat]:.4f}"
                        for key in ("mAP", "NDS") for stat in ("mean", "sample_sd"))
        check(rounded == expected[model], model + ": manuscript mean/sample SD")
    for key, expected_gain in (("mAP", "5.59"), ("NDS", "4.73")):
        gains = [100 * (b[key] - a[key]) for a, b in zip(paired["P0"], paired["P1"])]
        check(all(gain > 0 for gain in gains), key + ": every pair improves")
        check(f"{mean(gains):.2f}" == expected_gain, key + ": manuscript gain")

    check(classwise["seeds"] == seeds, "class-wise seeds")
    class_rows = {row["class"]: row for row in classwise["classes"]}
    check(len(classwise["classes"]) == 22 and set(class_rows) == set(categories),
          "class-wise comparison coverage")
    for category, row in class_rows.items():
        a = [r["per_class_AP"][category] for r in paired["P0"]]
        b = [r["per_class_AP"][category] for r in paired["P1"]]
        close(row["P0_mean_AP"], mean(a), category + ": P0 mean")
        close(row["P1_mean_AP"], mean(b), category + ": P1 mean")
        close(row["delta_AP"], mean(b) - mean(a), category + ": mean delta")
        check(len(row["paired_deltas"]) == 3, category + ": three paired deltas")
        for actual, x, y in zip(row["paired_deltas"], a, b):
            close(actual, y - x, category + ": paired delta")
    improved = sum(row["delta_AP"] > 0 for row in class_rows.values())
    declined = sorted(c for c, row in class_rows.items() if row["delta_AP"] < 0)
    check(improved == 18, "18 improved class means")
    check(declined == ["Flag", "Gazebo", "Porta_potty", "Tent"], "all declining classes retained")
    check(sum(all(x > 0 for x in row["paired_deltas"]) for row in class_rows.values()) == 15,
          "15 classes improve in every pair")
    contribution = sum(class_rows[c]["delta_AP"] for c in ("Small_table", "Sitting_person", "Barrel"))
    contribution /= sum(row["delta_AP"] for row in class_rows.values())
    check(f"{100 * contribution:.1f}" == "49.2", "three largest class contributions")

    check(len(latency) == 4 and len({r["run_id"] for r in latency}) == 4, "four timing runs")
    for run in latency:
        name = run["run_id"]
        check(run["checkpoint_sha256"] == by_id[name]["checkpoint_sha256"]
              == sources["latency_" + name]["checkpoint_sha256"], name + ": timing checkpoint")
        check("RTX 4090" in run["device"] and run["batch_size"] == 1, name + ": timing setup")
        check(run["warmup_frames"] == len(run["warmup_model_ms"]) == 20, name + ": warm-up")
        durations = sorted(run["timed_model_ms"])
        check(run["measured_frames"] == len(durations) == 200, name + ": measured frames")
        check(all(math.isfinite(x) and x > 0 for x in durations + run["warmup_model_ms"]),
              name + ": positive durations")
        close(mean(durations), run["mean_ms"], name + ": timing mean", 1e-8)
        position = 0.95 * (len(durations) - 1)
        lo, hi = math.floor(position), math.ceil(position)
        p95 = durations[lo] + (position - lo) * (durations[hi] - durations[lo])
        close(p95, run["p95_ms"], name + ": timing P95", 1e-8)

    # Check the human-readable threshold and class tables against the JSON.
    protocol = (ROOT / "docs/evaluation_protocol.md").read_text(encoding="utf-8")
    details = (ROOT / "docs/experiment_details.md").read_text(encoding="utf-8")
    for category, thresholds in config["dist_ths"].items():
        line = "| " + category.replace("_", " ") + " | " + " | ".join(f"{x:.2f}" for x in thresholds) + " |"
        check(line in protocol, category + ": displayed thresholds")
    for category, row in class_rows.items():
        line = (f"| {category.replace('_', ' ')} | {row['P0_mean_AP']:.4f} | "
                f"{row['P1_mean_AP']:.4f} | {row['delta_AP']:+.4f} |")
        check(line in details, category + ": displayed class-wise values")
    for run in latency:
        line = (f"| {run['run_id']} | {run['mean_ms']:.2f} | {run['p95_ms']:.2f} | "
                f"{run['peak_allocated_MB']:.1f} |")
        check(line in details, run["run_id"] + ": displayed timing values")
    for run in [by_id["P0_seed2026"], by_id["P1_seed2026"], *accuracy[6:]]:
        frequency = run["frequency_K"] if run["frequency_K"] is not None else "--"
        line = f"| {run['id']} | {frequency} | {run['mAP']:.4f} | {run['NDS']:.4f} |"
        check(line in details, run["id"] + ": displayed accuracy values")

    return {"status": "PASS", "accuracy_runs": len(accuracy), "timing_runs": len(latency),
            "classes": len(categories), "paired_summary": summary,
            "classes_with_improved_mean_AP": improved, "classes_with_lower_mean_AP": declined,
            "scope": "Archived numerical consistency only; no new inference or training."}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, allow_nan=False))
