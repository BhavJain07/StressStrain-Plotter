#!/usr/bin/env python3
"""
Stress-Strain Plotter - Single-file Python implementation
Plots stress-strain data and calculates material properties:
- Tensile Strength, Young's Modulus, Yield Strength (0.2% offset)
- Toughness, Ductility, Resilience
"""

import argparse
import sys
from pathlib import Path
from typing import NamedTuple, Optional


class DataPoint(NamedTuple):
    stress: float
    strain: float


def add_data_point(data: list[DataPoint], stress: float, strain: float) -> list[DataPoint]:
    """Add a data point and return sorted data (by strain)."""
    new_data = data + [DataPoint(stress=stress, strain=strain)]
    return sorted(new_data, key=lambda p: p.strain)


def clear_data() -> list[DataPoint]:
    """Return empty data list."""
    return []


def calculate_tensile_strength(data: list[DataPoint]) -> float:
    """Tensile strength is the maximum stress."""
    if not data:
        return 0.0
    return max(p.stress for p in data)


def calculate_youngs_modulus(data: list[DataPoint]) -> float:
    """
    Young's modulus: slope of linear elastic region (first 1/3 of data).
    Uses least squares through origin (stress = E * strain) per ASTM E111.
    """
    if len(data) < 2:
        return 0.0
    linear_cutoff = max(2, (len(data) + 2) // 3)
    linear_region = [p for p in data[:linear_cutoff] if p.strain > 1e-12]
    if len(linear_region) < 2:
        return 0.0
    numerator = sum(p.stress * p.strain for p in linear_region)
    denominator = sum(p.strain * p.strain for p in linear_region)
    if abs(denominator) < 1e-12:
        return 0.0
    return numerator / denominator


def _find_yield_point(
    data: list[DataPoint], youngs_modulus: float, offset: float = 0.002
) -> tuple[float, float]:
    """
    Yield strength using 0.2% offset method.
    Finds the intersection of the stress-strain curve with a line parallel to the
    elastic region, offset by 0.2% strain. Returns (yield_stress, yield_strain).
    """
    if not data or youngs_modulus <= 0:
        return (0.0, 0.0)
    for i in range(1, len(data)):
        prev, curr = data[i - 1], data[i]
        line_prev = youngs_modulus * (prev.strain - offset)
        line_curr = youngs_modulus * (curr.strain - offset)
        if prev.stress > line_prev and curr.stress < line_curr:
            t = (prev.stress - line_prev) / (
                (prev.stress - line_prev) - (curr.stress - line_curr)
            )
            strain_y = prev.strain + t * (curr.strain - prev.strain)
            stress_y = prev.stress + t * (curr.stress - prev.stress)
            return (stress_y, strain_y)
    return (0.0, 0.0)


def calculate_yield_strength(data: list[DataPoint], youngs_modulus: float, offset: float = 0.002) -> float:
    """Yield strength (0.2% offset method)."""
    stress, _ = _find_yield_point(data, youngs_modulus, offset)
    return stress


def calculate_toughness(data: list[DataPoint]) -> float:
    """Toughness: area under stress-strain curve (trapezoidal integration)."""
    if len(data) < 2:
        return 0.0
    total = 0.0
    for i in range(1, len(data)):
        prev, curr = data[i - 1], data[i]
        total += (curr.strain - prev.strain) * (curr.stress + prev.stress) / 2
    return total


def calculate_ductility(data: list[DataPoint]) -> float:
    """Ductility: total elongation (last strain - first strain)."""
    if len(data) < 2:
        return 0.0
    return data[-1].strain - data[0].strain


def calculate_resilience(
    data: list[DataPoint], yield_strength: float, yield_strain: float = 0.0
) -> float:
    """Resilience: area under stress-strain curve up to yield point (strain)."""
    if len(data) < 2 or yield_strength <= 0:
        return 0.0
    total = 0.0
    for i in range(1, len(data)):
        prev, curr = data[i - 1], data[i]
        if curr.strain <= yield_strain:
            total += (curr.strain - prev.strain) * (curr.stress + prev.stress) / 2
        elif prev.strain < yield_strain:
            t = (yield_strain - prev.strain) / (curr.strain - prev.strain)
            stress_at_yield = prev.stress + t * (curr.stress - prev.stress)
            total += (yield_strain - prev.strain) * (stress_at_yield + prev.stress) / 2
            break
        else:
            break
    return total


def calculate_material_properties(data: list[DataPoint]) -> Optional[dict[str, str]]:
    """Calculate all material properties. Returns None if insufficient data."""
    if len(data) < 2:
        return None

    tensile_strength = calculate_tensile_strength(data)
    youngs_modulus = calculate_youngs_modulus(data)
    yield_strength, yield_strain = _find_yield_point(data, youngs_modulus)
    toughness = calculate_toughness(data)
    ductility = calculate_ductility(data)
    resilience = calculate_resilience(data, yield_strength, yield_strain)

    return {
        "tensile_strength": f"{tensile_strength:.2f}",
        "youngs_modulus": f"{youngs_modulus / 1000:.2f}",  # Convert to GPa
        "yield_strength": f"{yield_strength:.2f}",
        "toughness": f"{toughness:.4f}",
        "ductility": f"{ductility:.4f}",
        "resilience": f"{resilience:.4f}",
    }


def load_data_from_csv(path: str) -> list[DataPoint]:
    """Load stress,strain pairs from CSV. Expects header or first row as stress,strain."""
    data: list[DataPoint] = []
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        line = line.strip()
        if not line or line.lower().startswith("stress"):
            continue
        parts = line.split(",")
        if len(parts) >= 2:
            try:
                stress = float(parts[0].strip())
                strain = float(parts[1].strip())
                data.append(DataPoint(stress=stress, strain=strain))
            except ValueError:
                continue
    return sorted(data, key=lambda p: p.strain)


def plot_stress_strain(
    data: list[DataPoint],
    title: str = "Stress vs Strain",
    output_path: Optional[str] = None,
    show: bool = True,
) -> None:
    """Plot stress vs strain and optionally save to file."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is required for plotting. Install with: pip install matplotlib")
        sys.exit(1)

    if not data:
        print("No data to plot.")
        return

    strains = [p.strain for p in data]
    stresses = [p.stress for p in data]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(strains, stresses, "b-o", markersize=4, linewidth=1.5)
    ax.set_xlabel("Strain")
    ax.set_ylabel("Stress (MPa)")
    ax.set_title(title)
    ax.grid(True, linestyle="--", alpha=0.7)

    if output_path:
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Plot saved to {output_path}")

    if show:
        plt.show()
    else:
        plt.close()


def interactive_mode() -> None:
    """Interactive mode: add points, plot, calculate properties."""
    data: list[DataPoint] = []

    def print_properties() -> None:
        props = calculate_material_properties(data)
        if props:
            print("\nMaterial Properties:")
            print(f"  Tensile Strength: {props['tensile_strength']} MPa")
            print(f"  Young's Modulus: {props['youngs_modulus']} GPa")
            print(f"  Yield Strength (0.2% offset): {props['yield_strength']} MPa")
            print(f"  Toughness: {props['toughness']} MJ/m³")
            print(f"  Ductility: {props['ductility']} mm/mm")
            print(f"  Resilience: {props['resilience']} MJ/m³")
        else:
            print("\nAdd at least 2 data points to see material properties.")

    print("Stress-Strain Plotter (Interactive)")
    print("Commands: add, clear, plot, save <path>, properties, list, quit")
    print()

    while True:
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not cmd:
            continue

        if cmd == "quit" or cmd == "q" or cmd == "exit":
            break

        if cmd == "add" or cmd == "a":
            try:
                s = input("  Stress (MPa): ").strip()
                t = input("  Strain: ").strip()
                if s and t:
                    stress_val = float(s)
                    strain_val = float(t)
                    data = add_data_point(data, stress_val, strain_val)
                    print(f"  Added ({stress_val}, {strain_val}). Total points: {len(data)}")
                else:
                    print("  Invalid input.")
            except ValueError:
                print("  Invalid number.")

        elif cmd == "clear" or cmd == "c":
            data = clear_data()
            print("  Data cleared.")

        elif cmd == "list" or cmd == "l":
            if data:
                print("  Data points (stress, strain):")
                for i, p in enumerate(data):
                    print(f"    {i + 1}. {p.stress}, {p.strain}")
            else:
                print("  No data points.")

        elif cmd == "properties" or cmd == "p":
            print_properties()

        elif cmd == "plot":
            plot_stress_strain(data, title="Stress vs Strain")

        elif cmd.startswith("save "):
            path = cmd[5:].strip()
            if path:
                plot_stress_strain(data, output_path=path, show=False)
            else:
                print("  Usage: save <output_path>")

        else:
            print("  Unknown command. Use: add, clear, plot, save <path>, properties, list, quit")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stress-Strain Plotter: plot data and calculate material properties"
    )
    parser.add_argument(
        "-i", "--input",
        metavar="CSV",
        help="Input CSV file with stress,strain columns",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="PATH",
        help="Output path for plot (PNG, SVG, or PDF)",
    )
    parser.add_argument(
        "-t", "--title",
        default="Stress vs Strain",
        help="Plot title",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not display plot (only save if -o given)",
    )
    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
        return

    data: list[DataPoint] = []
    if args.input:
        path = Path(args.input)
        if not path.exists():
            print(f"Error: file not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        data = load_data_from_csv(str(path))
        print(f"Loaded {len(data)} data points from {args.input}")
    else:
        print("No input file. Use -i <csv> or --interactive for interactive mode.")
        parser.print_help()
        sys.exit(1)

    if not data:
        print("No valid data points.", file=sys.stderr)
        sys.exit(1)

    props = calculate_material_properties(data)
    if props:
        print("\nMaterial Properties:")
        print(f"  Tensile Strength: {props['tensile_strength']} MPa")
        print(f"  Young's Modulus: {props['youngs_modulus']} GPa")
        print(f"  Yield Strength (0.2% offset): {props['yield_strength']} MPa")
        print(f"  Toughness: {props['toughness']} MJ/m³")
        print(f"  Ductility: {props['ductility']} mm/mm")
        print(f"  Resilience: {props['resilience']} MJ/m³")

    plot_stress_strain(
        data,
        title=args.title,
        output_path=args.output or None,
        show=not args.no_show,
    )


if __name__ == "__main__":
    main()
