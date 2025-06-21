#!/usr/bin/env python3
"""
ArtiTech Stage 1 - Edge Detection CLI
Real PiDiNet + DDN Hybrid Pipeline Implementation

Usage:
    python -m src.cli.edge_infer --input path/to/image.jpg --output path/to/output.jpg
    python -m src.cli.edge_infer --input path/to/image.jpg --model pidinet --benchmark
"""

import click
import cv2
import numpy as np
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.edge_detection.pidinet_model import PiDiNetModel
from src.edge_detection.ddn_model import DDNModel
from src.edge_detection.fusion import EdgeFusion


@click.command()
@click.option("--input", "-i", required=True, help="Input image path")
@click.option("--output", "-o", help="Output image path (optional)")
@click.option(
    "--model",
    "-m",
    type=click.Choice(["pidinet", "ddn", "fusion", "canny"], case_sensitive=False),
    default="pidinet",
    help="Edge detection model to use",
)
@click.option(
    "--threshold",
    "-t",
    default=0.5,
    type=float,
    help="Edge detection threshold (0.0-1.0, default: 0.5 for balanced quality)",
)
@click.option(
    "--device",
    "-d",
    default="auto",
    type=click.Choice(["auto", "cpu", "cuda", "mps"], case_sensitive=False),
    help="Computation device",
)
@click.option("--benchmark", is_flag=True, help="Run performance benchmark")
@click.option("--num-runs", default=50, type=int, help="Number of benchmark runs")
@click.option(
    "--model-variant",
    default="standard",
    type=click.Choice(["tiny", "small", "standard"], case_sensitive=False),
    help="PiDiNet model variant (default: standard for optimal quality)",
)
@click.option("--save-intermediate", is_flag=True, help="Save intermediate results")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(
    input: str,
    output: Optional[str],
    model: str,
    threshold: float,
    device: str,
    benchmark: bool,
    num_runs: int,
    model_variant: str,
    save_intermediate: bool,
    verbose: bool,
):
    """
    ArtiTech Stage 1 Edge Detection CLI

    Performs edge detection using PiDiNet, DDN, or hybrid fusion models.
    Optimized for real-time performance with <50ms target latency.
    """

    # Validate input
    if not os.path.exists(input):
        click.echo(f"❌ Error: Input file '{input}' not found", err=True)
        sys.exit(1)

    # Load image
    try:
        image = cv2.imread(input)
        if image is None:
            raise ValueError("Could not load image")

        if verbose:
            click.echo(f"📷 Loaded image: {image.shape[1]}x{image.shape[0]} pixels")

    except Exception as e:
        click.echo(f"❌ Error loading image: {e}", err=True)
        sys.exit(1)

    # Initialize model
    try:
        edge_model = _initialize_model(model, model_variant, device, verbose)
    except Exception as e:
        click.echo(f"❌ Error initializing model: {e}", err=True)
        sys.exit(1)

    # Run benchmark if requested
    if benchmark:
        _run_benchmark(edge_model, image, num_runs, verbose)
        return

    # Perform edge detection
    try:
        start_time = time.time()

        if model.lower() == "canny":
            result = _run_canny_detection(image, threshold)
        else:
            result = edge_model.predict(image, threshold=threshold)

        total_time = (time.time() - start_time) * 1000

        if verbose:
            click.echo(f"⚡ Total processing time: {total_time:.2f}ms")
            if "inference_time_ms" in result:
                click.echo(
                    f"🧠 Model inference time: {result['inference_time_ms']:.2f}ms"
                )

    except Exception as e:
        click.echo(f"❌ Error during inference: {e}", err=True)
        sys.exit(1)

    # Save results
    try:
        _save_results(result, input, output, save_intermediate, verbose)

        # Performance summary
        if not benchmark:
            _print_performance_summary(result, total_time)

    except Exception as e:
        click.echo(f"❌ Error saving results: {e}", err=True)
        sys.exit(1)


def _initialize_model(model: str, variant: str, device: str, verbose: bool):
    """Initialize the specified edge detection model"""

    if model.lower() == "canny":
        return None  # Canny doesn't need initialization

    # Get model weights path
    model_path = _get_model_path(model, variant)

    if verbose:
        click.echo(f"🔧 Initializing {model.upper()} model...")
        click.echo(f"📁 Model weights: {model_path}")
        click.echo(f"💻 Device: {device}")

    if model.lower() == "pidinet":
        return PiDiNetModel(
            model_path=model_path,
            device=device,
            use_converted=False,  # Use original model for weight loading
            use_sa=True,  # Use spatial attention
            use_dil=True,  # Use dilated convolutions
            model_variant=variant,
        )

    elif model.lower() == "ddn":
        return DDNModel(model_path=model_path, device=device)

    elif model.lower() == "fusion":
        # Initialize both models for fusion
        pidinet_path = _get_model_path("pidinet", variant)
        ddn_path = _get_model_path("ddn", "standard")

        pidinet_model = PiDiNetModel(model_path=pidinet_path, device=device)
        ddn_model = DDNModel(model_path=ddn_path, device=device)

        return EdgeFusion(pidinet_model, ddn_model)

    else:
        raise ValueError(f"Unknown model: {model}")


def _get_model_path(model: str, variant: str) -> Optional[str]:
    """Get the path to model weights"""

    model_dir = project_root / "models"

    if model.lower() == "pidinet":
        if variant == "tiny":
            return str(model_dir / "pidinet" / "table5_pidinet-tiny.pth")
        elif variant == "small":
            return str(model_dir / "pidinet" / "table5_pidinet-small.pth")
        else:  # standard
            return str(model_dir / "pidinet" / "table5_pidinet.pth")

    elif model.lower() == "ddn":
        return str(model_dir / "ddn" / "ddn_weights.pth")

    return None


def _run_canny_detection(image: np.ndarray, threshold: float) -> Dict[str, Any]:
    """Run Canny edge detection as fallback"""
    start_time = time.time()

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur
    blurred = cv2.GaussianBlur(gray, (5, 5), 1.4)

    # Canny edge detection
    low_threshold = int(threshold * 100)
    high_threshold = int(threshold * 200)
    edges = cv2.Canny(blurred, low_threshold, high_threshold)

    inference_time = (time.time() - start_time) * 1000

    return {
        "edge_map": edges,
        "edge_map_thresh": edges,
        "inference_time_ms": inference_time,
        "threshold": threshold,
        "input_shape": image.shape[:2],
        "model_config": {
            "model": "canny",
            "low_threshold": low_threshold,
            "high_threshold": high_threshold,
        },
    }


def _run_benchmark(model, image: np.ndarray, num_runs: int, verbose: bool):
    """Run performance benchmark"""

    click.echo(f"🏃 Running benchmark with {num_runs} iterations...")
    click.echo("=" * 50)

    if model is None:  # Canny
        times = []
        for i in range(num_runs):
            result = _run_canny_detection(image, 0.5)
            times.append(result["inference_time_ms"])

            if verbose and (i + 1) % 10 == 0:
                click.echo(f"Completed {i + 1}/{num_runs} runs")

        # Calculate statistics
        times = np.array(times)
        stats = {
            "mean_time_ms": float(np.mean(times)),
            "median_time_ms": float(np.median(times)),
            "min_time_ms": float(np.min(times)),
            "max_time_ms": float(np.max(times)),
            "std_time_ms": float(np.std(times)),
            "total_inferences": len(times),
        }

        target_time_ms = 50.0
        meets_target = stats["mean_time_ms"] <= target_time_ms

    else:
        stats = model.benchmark(image, num_runs)
        target_time_ms = stats.get("target_time_ms", 50.0)
        meets_target = stats.get("meets_target", False)

    # Print results
    click.echo("\n📊 Benchmark Results:")
    click.echo("-" * 30)
    click.echo(f"Mean time:   {stats['mean_time_ms']:.2f}ms")
    click.echo(f"Median time: {stats['median_time_ms']:.2f}ms")
    click.echo(f"Min time:    {stats['min_time_ms']:.2f}ms")
    click.echo(f"Max time:    {stats['max_time_ms']:.2f}ms")
    click.echo(f"Std dev:     {stats['std_time_ms']:.2f}ms")
    click.echo(f"Total runs:  {stats['total_inferences']}")
    click.echo("-" * 30)
    click.echo(f"Target:      {target_time_ms}ms")
    click.echo(f"Status:      {'✅ PASS' if meets_target else '❌ FAIL'}")

    if meets_target:
        speedup = target_time_ms / stats["mean_time_ms"]
        click.echo(f"Speedup:     {speedup:.1f}x faster than target")


def _save_results(
    result: Dict[str, Any],
    input_path: str,
    output_path: Optional[str],
    save_intermediate: bool,
    verbose: bool,
):
    """Save edge detection results"""

    # Determine output path
    if output_path is None:
        input_stem = Path(input_path).stem
        output_path = f"{input_stem}_edges.jpg"

    # Save main result
    edge_map = result.get("edge_map_thresh", result.get("edge_map"))
    cv2.imwrite(output_path, edge_map)

    if verbose:
        click.echo(f"💾 Saved edge map: {output_path}")

    # Save intermediate results if requested
    if save_intermediate and "edge_map" in result:
        base_path = Path(output_path).stem

        # Save raw edge map
        raw_path = f"{base_path}_raw.jpg"
        cv2.imwrite(raw_path, result["edge_map"])

        if verbose:
            click.echo(f"💾 Saved raw edge map: {raw_path}")


def _print_performance_summary(result: Dict[str, Any], total_time: float):
    """Print performance summary"""

    click.echo("\n⚡ Performance Summary:")
    click.echo("-" * 25)

    if "inference_time_ms" in result:
        click.echo(f"Model inference: {result['inference_time_ms']:.2f}ms")

    click.echo(f"Total time:      {total_time:.2f}ms")

    # Check against targets
    target_client = 30.0  # PiDiNet client target
    target_total = 50.0  # Total pipeline target

    if "inference_time_ms" in result:
        model_time = result["inference_time_ms"]
        if model_time <= target_client:
            click.echo(f"Client target:   ✅ {model_time:.2f}ms ≤ {target_client}ms")
        else:
            click.echo(f"Client target:   ❌ {model_time:.2f}ms > {target_client}ms")

    if total_time <= target_total:
        click.echo(f"Total target:    ✅ {total_time:.2f}ms ≤ {target_total}ms")
    else:
        click.echo(f"Total target:    ❌ {total_time:.2f}ms > {target_total}ms")

    # Model configuration
    if "model_config" in result:
        config = result["model_config"]
        click.echo(f"\n🔧 Configuration:")
        for key, value in config.items():
            click.echo(f"  {key}: {value}")


if __name__ == "__main__":
    main()
