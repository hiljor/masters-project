import re
import sys
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from pathlib import Path
import numpy as np

# Ensure the repo root is importable so `data.generate` (which lives at the
# repo root's data/ directory, not under src/) can be imported regardless of
# how this module is invoked.
_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from data.generate import map_display_title

RANGE_LEGEND_LABEL = 'Min\u2013max range (across repeated runs)'


def _add_variation_band(ax, x, data, color, alpha=0.2):
    """Shade the min-max runtime range around a line.

    The benchmark timer (horse_algos.timer.timer) repeats each
    (algorithm, dataset, k) measurement many times (default 30 iterations)
    and records summary statistics -- including the per-point 'Min (s)'
    and 'Max (s)' -- in the results CSV alongside the raw runtimes. This
    draws a shaded band between the observed minimum and maximum runtime
    at each x position, so the variation across the repeated measurements
    is visible alongside the plotted line (which shows the median).

    Args:
        ax: The matplotlib Axes to draw on.
        x: The x-values, aligned (same index) with `data`.
        data: DataFrame slice containing the 'Min (s)' / 'Max (s)' columns
            for the points being plotted.
        color: Fill color, normally the color of the accompanying line so
            the band visually belongs to that series.
        alpha: Transparency of the shaded band.
    """
    lower = pd.to_numeric(data['Min (s)'], errors='coerce')
    upper = pd.to_numeric(data['Max (s)'], errors='coerce')
    mask = lower.notna() & upper.notna()
    if not mask.any():
        return
    ax.fill_between(x[mask], lower[mask], upper[mask],
                     color=color, alpha=alpha, linewidth=0, zorder=1)


def _range_legend_handle():
    """A generic legend patch explaining the shaded variation bands."""
    return Patch(facecolor='gray', alpha=0.25, label=RANGE_LEGEND_LABEL)

def load_and_visualize_benchmarks():
    """Load benchmark results and create visualizations with time vs k value."""
    
    # Find the results CSV file
    repo_root = Path(__file__).resolve().parents[3]
    csv_path = repo_root / "results" / "benchmark_results.csv"
    
    if not csv_path.exists():
        print(f"Benchmark file not found at {csv_path}")
        return
    
    # Load data
    df = pd.read_csv(csv_path)
    
    # Exclude the Generated_* size-test datasets from the per-dataset
    # algorithm comparison plots. Those datasets are visualised separately
    # by load_and_visualize_size_test, which plots node count vs time.
    df = df[~df['Dataset'].astype(str).str.startswith('Generated_')]
    
    # Convert 'DNF' (Did Not Finish) to NaN for plotting
    # Extract numeric time values, treating 'DNF' as missing data.
    # The timer records multiple iterations per run and stores summary
    # statistics; we plot the median wall-clock time (time.perf_counter_ns)
    # from horse_algos.timer.timer.
    time_col = 'Median (s)'
    df['Time_numeric'] = pd.to_numeric(df[time_col], errors='coerce')
    
    # Get unique datasets
    datasets = df['Dataset'].unique()
    
    # Create a figure for each dataset
    for dataset in datasets:
        dataset_data = df[df['Dataset'] == dataset]
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(12, 7))
        
        # Get unique algorithms for this dataset
        algorithms = dataset_data['Algorithm'].unique()
        
        # Plot each algorithm
        for algo in algorithms:
            algo_data = dataset_data[dataset_data['Algorithm'] == algo].sort_values('k')
            
            # Only plot points that represent genuine completed timings:
            # exclude ERROR rows (e.g. "too expensive", MemoryError,
            # BrokenProcessPool) whose recorded time of 0 is not a real
            # measurement, and exclude timed-out (DNF) runs.
            error_mask = algo_data['Result'].str.startswith('ERROR:').fillna(False)
            valid_data = algo_data[~error_mask].sort_values('k')
            
            if len(valid_data) > 0:
                line, = ax.plot(valid_data['k'], valid_data['Time_numeric'], 
                       marker='o', label=algo, linewidth=2, markersize=6)
                # Shade the min-max runtime range (from the many repeated
                # timed iterations per k value) around the median line.
                _add_variation_band(ax, valid_data['k'], valid_data, line.get_color())
        
        # Customize plot
        ax.set_xlabel('k Value', fontsize=12, fontweight='bold')
        ax.set_ylabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax.set_title(f'Algorithm Performance: {map_display_title(dataset)}', fontsize=14, fontweight='bold')
        # Legend scaled up by 50% so the algorithm names are readable on A4.
        handles, labels = ax.get_legend_handles_labels()
        handles.append(_range_legend_handle())
        labels.append(RANGE_LEGEND_LABEL)
        ax.legend(handles=handles, labels=labels, loc='best', fontsize=15)
        ax.grid(True, alpha=0.3)
        ax.set_xticks(sorted(df['k'].unique()))
        
        # Set y-axis limit to show DNF threshold
        ax.set_ylim(bottom=0, top=65)
        
        plt.tight_layout()
        
        # Save figure
        output_dir = repo_root / "data" / "img"
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_dataset_name = dataset.replace('.txt', '').replace(' ', '_')
        fig.savefig(output_dir / f"{safe_dataset_name}_performance.png", dpi=150)
        print(f"Saved: {safe_dataset_name}_performance.png")
        
        plt.show()
    
    # Create a combined comparison plot.
    # Use a 2-column grid: the top-left cell holds one common legend with the
    # algorithm colors/names, and the datasets occupy the remaining cells
    # (row-major, starting in the cell directly to the right of the legend).
    n_cols = 2
    n_rows = (len(datasets) + n_cols - 1) // n_cols
    # Compress the subplot sizes so text renders larger on A4: per-subplot
    # height reduced 20% and per-subplot width reduced 30% vs. a single
    # column of 14 x 5 subplots.
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(14 * 0.7, 5 * 0.8 * n_rows))
    axes = axes.flatten()
    
    # Canonical algorithm order and matching colors so every subplot and the
    # shared legend use the same colors for the same algorithm.
    all_algorithms = list(dict.fromkeys(df['Algorithm'].tolist()))
    prop_cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
    algo_colors = {algo: prop_cycle[i % len(prop_cycle)] for i, algo in enumerate(all_algorithms)}
    
    # Hide any unused subplot slots in the grid (cell 0 is the legend).
    for ax in axes[1 + len(datasets):]:
        ax.set_visible(False)
    
    # Common legend in the top-left cell.
    legend_ax = axes[0]
    legend_ax.set_axis_off()
    legend_handles = [
        Line2D([], [], color=algo_colors[algo], marker='o', label=algo,
               linewidth=2.6, markersize=6.5)
        for algo in all_algorithms
    ]
    legend_handles.append(_range_legend_handle())
    legend_ax.legend(handles=legend_handles, loc='center', fontsize=13,
                     title_fontsize=13, frameon=True, title='Algorithms')
    
    for idx, dataset in enumerate(datasets):
        ax = axes[1 + idx]
        dataset_data = df[df['Dataset'] == dataset]
        
        for algo in all_algorithms:
            if algo not in dataset_data['Algorithm'].values:
                continue
            algo_data = dataset_data[dataset_data['Algorithm'] == algo].sort_values('k')
            error_mask = algo_data['Result'].str.startswith('ERROR:').fillna(False)
            valid_data = algo_data[~error_mask].sort_values('k')
            
            if len(valid_data) > 0:
                ax.plot(valid_data['k'], valid_data['Time_numeric'],
                        color=algo_colors[algo], marker='o', linewidth=2, markersize=5)
                # Shade the min-max runtime range around each algorithm's
                # line using its designated color.
                _add_variation_band(ax, valid_data['k'], valid_data, algo_colors[algo])
        
        ax.set_xlabel('k Value', fontsize=11, fontweight='bold')
        ax.set_ylabel('Time (seconds)', fontsize=11, fontweight='bold')
        ax.set_title(f'{map_display_title(dataset)}', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_xticks(sorted(df['k'].unique()))
        ax.set_ylim(bottom=0, top=65)
    
    # Cut subplot padding by 20% vertically and 30% horizontally
    # (matplotlib's default tight_layout pad is 1.08).
    plt.tight_layout(h_pad=1.08 * 0.8, w_pad=1.08 * 0.7)
    fig.savefig(repo_root / "data" / "img" / "all_datasets_comparison.png", dpi=150)
    print(f"Saved: all_datasets_comparison.png")
    plt.show()

def load_and_visualize_size_test():
    """Load the size-test results and plot node count vs time (k=8).
    
    The size-test datasets are named SizeTest_NxN and all use k=8. The
    number of nodes in such a graph is N*N (e.g. SizeTest_22x22 contains
    22*22 = 484 nodes). This function plots the median wall-clock time
    (from the 'Median (s)' column, computed over many repeated timed runs
    by horse_algos.timer.timer) for the C++ Important Separators and
    OR-Tools algorithms against the node count, with a shaded band showing
    the min-max runtime range observed across those repeated runs.
    """
    repo_root = Path(__file__).resolve().parents[3]
    csv_path = repo_root / "results" / "size_test_results.csv"
    
    if not csv_path.exists():
        print(f"Size test file not found at {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    
    time_col = 'Median (s)'
    df['Time_numeric'] = pd.to_numeric(df[time_col], errors='coerce')
    
    # Only the constant k=8 size-test runs
    df = df[df['k'] == 8].copy()
    
    # Exclude failed runs, which do not represent genuine timings
    df = df[~df['Result'].astype(str).str.startswith('ERROR:')]
    
    # Parse the node count from the dataset name: "SizeTest_22x22" -> 484
    def extract_node_count(dataset_name: str) -> float:
        match = re.search(r'SizeTest_(\d+)x(\d+)', str(dataset_name))
        if match:
            return int(match.group(1)) * int(match.group(2))
        return float('nan')
    
    df['NodeCount'] = df['Dataset'].apply(extract_node_count)
    df = df.dropna(subset=['NodeCount', 'Time_numeric'])
    
    # Only plot the C++ Important Separators and OR-Tools algorithms
    algorithms = ['Important Separators (C++)', 'MILP (OR-Tools)']
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    for algo in algorithms:
        algo_data = df[df['Algorithm'] == algo].sort_values('NodeCount')
        if len(algo_data) > 0:
            line, = ax.plot(algo_data['NodeCount'], algo_data['Time_numeric'],
                    marker='o', label=algo, linewidth=2, markersize=6)
            # Shade the min-max runtime range (from the many repeated
            # timed iterations per graph size) around the median line.
            _add_variation_band(ax, algo_data['NodeCount'], algo_data, line.get_color())
    
    ax.set_xlabel('Number of Nodes', fontsize=12, fontweight='bold')
    ax.set_ylabel('Time (CPU seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Size Test: Runtime vs Graph Size (k=8)', fontsize=14, fontweight='bold')
    # Legend scaled up by 50% so the algorithm names are readable on A4.
    handles, labels = ax.get_legend_handles_labels()
    handles.append(_range_legend_handle())
    labels.append(RANGE_LEGEND_LABEL)
    ax.legend(handles=handles, labels=labels, loc='best', fontsize=15)
    ax.grid(True, alpha=0.3)
    # Node counts span 100 to ~10 million and runtimes span ~0.1 ms to
    # ~740 s, so use log scales to keep the trend visible.
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    plt.tight_layout()
    output_dir = repo_root / "data" / "img"
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / "size_test_comparison.png", dpi=150)
    print("Saved: size_test_comparison.png")
    plt.show()


if __name__ == "__main__":
    load_and_visualize_benchmarks()
    load_and_visualize_size_test()