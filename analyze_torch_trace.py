#!/usr/bin/env python3
"""Analyze torch profiler traces with multi-rank aggregation.

Loads ALL trace files in a directory (one per rank/worker in TP/MP runs),
prints per-rank summaries, then a merged global top-N.

Usage:
    python3 scripts/analyze_torch_trace.py <trace_dir> [top_n]
"""

import json
import sys
from pathlib import Path


def _load_single_trace(trace_file: Path) -> dict:
    if str(trace_file).endswith(".gz"):
        import gzip
        with gzip.open(trace_file, "rt") as f:
            return json.load(f)
    else:
        with open(trace_file) as f:
            return json.load(f)


def load_all_traces(trace_dir: str) -> list[tuple[str, dict]]:
    """Return list of (filename, trace_data) for every trace in the directory."""
    trace_path = Path(trace_dir)
    json_files = sorted(trace_path.glob("*.json")) + sorted(trace_path.glob("*.json.gz"))
    if not json_files:
        print(f"No trace files found in {trace_dir}")
        sys.exit(1)

    results = []
    for f in json_files:
        print(f"Loading: {f.name}")
        results.append((f.name, _load_single_trace(f)))
    print(f"Loaded {len(results)} trace file(s)")
    return results


def extract_cuda_kernels(trace: dict, top_n: int = 30) -> list[dict]:
    events = trace.get("traceEvents", [])
    kernels = []
    for ev in events:
        cat = ev.get("cat", "")
        if cat in ("kernel", "gpu_memcpy", "cuda_runtime"):
            kernels.append({"name": ev.get("name", ""), "dur_us": ev.get("dur", 0)})
    kernels.sort(key=lambda x: -x["dur_us"])
    return kernels[:top_n]


def merge_events(traces: list[tuple[str, dict]]) -> dict:
    merged = []
    for _, data in traces:
        merged.extend(data.get("traceEvents", []))
    return {"traceEvents": merged}


def check_fp8_gemm(kernels: list[dict]) -> list[dict]:
    fp8_indicators = ["fp8", "e4m3", "e5m2", "f8", "cutlass_fp8", "sm90_xmma", "cublas_fp8", "cublasLt"]
    return [k for k in kernels if any(ind in k["name"].lower() for ind in fp8_indicators)]


def print_kernel_table(kernels: list[dict], top_n: int) -> None:
    for i, k in enumerate(kernels[:top_n], 1):
        print(f"  {i:3d}. {k['dur_us'] / 1000:10.3f} ms  {k['name'][:100]}")


def print_category_breakdown(all_kernels: list[dict]) -> None:
    categories = {
        "GEMM/MatMul": ["gemm", "cublas", "cutlass", "xmma", "matmul"],
        "Attention": ["attention", "flash", "fmha", "sdpa"],
        "Elementwise": ["elementwise", "vectorized", "unrolled"],
        "Reduction": ["reduce", "softmax", "layernorm", "rmsnorm"],
        "Memory": ["memcpy", "memset"],
    }
    total_us = sum(k["dur_us"] for k in all_kernels) or 1
    for cat_name, keywords in categories.items():
        cat_kernels = [k for k in all_kernels if any(kw in k["name"].lower() for kw in keywords)]
        if cat_kernels:
            total_ms = sum(k["dur_us"] for k in cat_kernels) / 1000
            pct = 100 * sum(k["dur_us"] for k in cat_kernels) / total_us
            print(f"  {cat_name:20s}: {total_ms:10.1f} ms ({pct:5.1f}%)  [{len(cat_kernels)} kernels]")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_torch_trace.py <trace_dir> [top_n]")
        sys.exit(1)

    trace_dir = sys.argv[1]
    top_n = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    traces = load_all_traces(trace_dir)

    # Per-rank summaries
    if len(traces) > 1:
        print(f"\n{'=' * 70}")
        print(f"  Per-Rank Summaries ({len(traces)} ranks)")
        print(f"{'=' * 70}")
        for fname, data in traces:
            kernels = extract_cuda_kernels(data, top_n=10000)
            total_ms = sum(k["dur_us"] for k in kernels) / 1000
            fp8 = check_fp8_gemm(kernels)
            fp8_ms = sum(k["dur_us"] for k in fp8) / 1000
            print(f"\n  {fname}:")
            print(f"    Total GPU time: {total_ms:.1f} ms  |  Kernels: {len(kernels)}  |  FP8 kernels: {len(fp8)} ({fp8_ms:.1f} ms)")
            top5 = extract_cuda_kernels(data, top_n=5)
            for i, k in enumerate(top5, 1):
                print(f"      {i}. {k['dur_us'] / 1000:8.3f} ms  {k['name'][:80]}")

    # Merged global analysis
    merged = merge_events(traces)

    print(f"\n{'=' * 70}")
    print(f"  Global Top-{top_n} CUDA Kernels (merged across {len(traces)} rank(s))")
    print(f"{'=' * 70}")

    kernels = extract_cuda_kernels(merged, top_n=top_n)
    if not kernels:
        print("  No CUDA kernel events found.")
        return

    print_kernel_table(kernels, top_n)

    # FP8 analysis
    print(f"\n{'=' * 70}")
    print("  FP8 GEMM Path Analysis (global)")
    print(f"{'=' * 70}")

    all_kernels = extract_cuda_kernels(merged, top_n=10000)
    fp8_kernels = check_fp8_gemm(all_kernels)

    if fp8_kernels:
        total_fp8_us = sum(k["dur_us"] for k in fp8_kernels)
        total_all_us = sum(k["dur_us"] for k in all_kernels) or 1
        print(f"  FP8 kernels found: {len(fp8_kernels)}")
        print(f"  FP8 total time: {total_fp8_us / 1000:.3f} ms ({100 * total_fp8_us / total_all_us:.1f}% of GPU time)")
        print("\n  Top FP8 kernels:")
        for i, k in enumerate(sorted(fp8_kernels, key=lambda x: -x["dur_us"])[:15], 1):
            print(f"    {i:3d}. {k['dur_us'] / 1000:10.3f} ms  {k['name'][:100]}")
        print("\n  Conclusion: FP8 GEMM path is ACTIVE")
    else:
        gemm_keywords = ["gemm", "cublas", "cutlass", "xmma", "matmul"]
        gemm_kernels = [k for k in all_kernels if any(g in k["name"].lower() for g in gemm_keywords)]
        if gemm_kernels:
            print(f"  WARNING: No FP8-specific kernels found, but {len(gemm_kernels)} GEMM kernels detected.")
            print("  Conclusion: FP8 GEMM path may NOT be active.")
        else:
            print("  No GEMM kernels found. Trace may be incomplete.")

    print(f"\n{'=' * 70}")
    print("  Kernel Category Breakdown (global)")
    print(f"{'=' * 70}")
    print_category_breakdown(all_kernels)


if __name__ == "__main__":
    main()
