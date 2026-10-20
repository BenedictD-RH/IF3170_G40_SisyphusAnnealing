import os
import sys
import json
import subprocess
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Union, Dict, Any, List, Tuple

if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()


@dataclass
class PlotTheme:
    """Konfigurasi tema tampilan grafik."""
    name: str = "academic"
    bg_color: str = "#ffffff"
    text_color: str = "#222222"
    primary_line_color: str = "#1f77b4"     
    secondary_line_color: str = "#d62728"   
    best_marker_color: str = "#2ca02c"      
    start_marker_color: str = "#7f7f7f"     
    grid_color: str = "#e0e0e0"
    grid_style: str = "--"
    grid_alpha: float = 0.7
    font_family: str = "sans-serif"
    title_font_size: int = 12
    label_font_size: int = 10
    legend_font_size: int = 9
    line_width: float = 1.6
    figure_dpi: int = 100


THEMES: Dict[str, PlotTheme] = {
    "academic": PlotTheme(
        name="academic",
        bg_color="#ffffff",
        text_color="#1a1a1a",
        primary_line_color="#1f77b4",
        secondary_line_color="#d62728",
        best_marker_color="#2ca02c",
        start_marker_color="#7f7f7f",
        grid_color="#e5e5e5",
        grid_alpha=0.8,
    ),
    "dark": PlotTheme(
        name="dark",
        bg_color="#1e1e1e",
        text_color="#f0f0f0",
        primary_line_color="#4da6ff",
        secondary_line_color="#ff6b6b",
        best_marker_color="#51cf66",
        start_marker_color="#adb5bd",
        grid_color="#333333",
        grid_alpha=0.6,
    ),
    "minimal": PlotTheme(
        name="minimal",
        bg_color="#ffffff",
        text_color="#333333",
        primary_line_color="#2b2b2b",
        secondary_line_color="#737373",
        best_marker_color="#000000",
        start_marker_color="#888888",
        grid_color="#f0f0f0",
        grid_alpha=0.5,
    ),
}


def _get_marker_config(n_points: int) -> Tuple[Optional[str], float]:
    if n_points <= 50:
        return "o", 4.0
    elif n_points <= 200:
        return "o", 2.0
    elif n_points <= 500:
        return ".", 1.5
    return None, 0.0


class BasePlotTemplate(ABC):

    def __init__(self, theme: Optional[Union[str, PlotTheme]] = None, export_path: Optional[str] = None):
        if isinstance(theme, PlotTheme):
            self.theme = theme
        elif isinstance(theme, str) and theme.lower() in THEMES:
            self.theme = THEMES[theme.lower()]
        else:
            self.theme = THEMES["academic"]
        self.export_path = export_path
        self.fig = None
        self.axes: List[Any] = []

    def apply_theme_to_axis(self, ax) -> None:
        ax.set_facecolor(self.theme.bg_color)
        ax.grid(
            True,
            linestyle=self.theme.grid_style,
            color=self.theme.grid_color,
            alpha=self.theme.grid_alpha
        )
        ax.tick_params(colors=self.theme.text_color, labelsize=self.theme.label_font_size - 1)
        for spine in ax.spines.values():
            spine.set_color(self.theme.text_color)
            spine.set_alpha(0.3)

    @abstractmethod
    def create_figure(self, plt) -> Any:
        pass

    @abstractmethod
    def draw_content(self, plt, data: Any) -> None:
        pass

    def render(self, data: Any, show: bool = True) -> Any:
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("[WARNING] matplotlib is not installed. Please run: pip install matplotlib")
            return None

        self.fig = self.create_figure(plt)
        self.fig.patch.set_facecolor(self.theme.bg_color)
        try:
            if hasattr(self.fig.canvas, "manager") and self.fig.canvas.manager:
                self.fig.canvas.manager.set_window_title("Optimization Visualizer - IF3170")
        except Exception:
            pass

        self.draw_content(plt, data)
        plt.tight_layout()
        if self.export_path:
            self.export(self.export_path)

        if show:
            plt.show()
            plt.close(self.fig)

        return self.fig

    def export(self, filepath: str, dpi: Optional[int] = None) -> None:
        """Menyimpan grafik ke file (PNG, PDF, SVG, dll)."""
        if self.fig is None:
            return
        out_dpi = dpi or self.theme.figure_dpi
        dirname = os.path.dirname(os.path.abspath(filepath))
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        self.fig.savefig(
            filepath,
            dpi=out_dpi,
            facecolor=self.theme.bg_color,
            edgecolor="none",
            bbox_inches="tight"
        )
        print(f"[INFO] Plot exported successfully to: {filepath}")


class SingleMetricPlotTemplate(BasePlotTemplate):

    def create_figure(self, plt) -> Any:
        fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=self.theme.figure_dpi)
        self.axes = [ax]
        self.apply_theme_to_axis(ax)
        return fig

    def draw_content(self, plt, data: Any) -> None:
        ax = self.axes[0]
        objs = data if isinstance(data, list) else data.get("objectives", [])
        n_points = len(objs)
        if n_points == 0:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", color=self.theme.text_color)
            return

        iterations = list(range(n_points))
        marker, m_size = _get_marker_config(n_points)

        ax.plot(
            iterations,
            objs,
            color=self.theme.primary_line_color,
            linewidth=self.theme.line_width,
            marker=marker,
            markersize=m_size,
            label="Objective Value"
        )

        ax.scatter([0], [objs[0]], color=self.theme.start_marker_color, s=35, zorder=4, label=f"Initial: {objs[0]:,.1f}")

        best_idx, best_val = max(enumerate(objs), key=lambda x: x[1])
        ax.scatter(
            [best_idx],
            [best_val],
            color=self.theme.best_marker_color,
            s=55,
            zorder=5,
            label=f"Best: {best_val:,.1f} (iter {best_idx})"
        )
        imprv = best_val - objs[0]
        summary_txt = f"Total Iter: {n_points}\nInitial: {objs[0]:,.1f}\nBest: {best_val:,.1f}\nImprovement: {imprv:+,.1f}"
        ax.text(
            0.02, 0.96, summary_txt,
            transform=ax.transAxes,
            fontsize=self.theme.legend_font_size,
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=self.theme.bg_color, edgecolor=self.theme.grid_color, alpha=0.9),
            color=self.theme.text_color
        )

        ax.set_title("Optimization History: Objective vs Iteration", fontsize=self.theme.title_font_size, color=self.theme.text_color, pad=10)
        ax.set_xlabel("Iteration", fontsize=self.theme.label_font_size, color=self.theme.text_color)
        ax.set_ylabel("Objective Function", fontsize=self.theme.label_font_size, color=self.theme.text_color)
        ax.legend(fontsize=self.theme.legend_font_size, loc="lower right", facecolor=self.theme.bg_color, edgecolor=self.theme.grid_color)


class SimulatedAnnealingPlotTemplate(BasePlotTemplate):

    def create_figure(self, plt) -> Any:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.0, 7.0), sharex=True, dpi=self.theme.figure_dpi)
        self.axes = [ax1, ax2]
        self.apply_theme_to_axis(ax1)
        self.apply_theme_to_axis(ax2)
        return fig

    def draw_content(self, plt, data: Any) -> None:
        ax1, ax2 = self.axes[0], self.axes[1]
        objs = data.get("objectives", [])
        probs = data.get("probabilities", [])
        stuck_metrics = data.get("stuck_metrics", {})
        n_points = len(objs)

        if n_points == 0:
            ax1.text(0.5, 0.5, "No data available", ha="center", va="center", color=self.theme.text_color)
            return

        iters = list(range(n_points))
        marker, m_size = _get_marker_config(n_points)
        ax1.plot(
            iters,
            objs,
            color=self.theme.primary_line_color,
            linewidth=self.theme.line_width,
            marker=marker,
            markersize=m_size,
            label="Current Objective"
        )

        ax1.scatter([0], [objs[0]], color=self.theme.start_marker_color, s=35, zorder=4, label=f"Initial: {objs[0]:,.1f}")

        best_idx, best_val = max(enumerate(objs), key=lambda x: x[1])
        ax1.scatter(
            [best_idx],
            [best_val],
            color=self.theme.best_marker_color,
            s=55,
            zorder=5,
            label=f"Best: {best_val:,.1f} (iter {best_idx})"
        )

        imprv = best_val - objs[0]
        sa_summary = f"Init: {objs[0]:,.1f} | Best: {best_val:,.1f} ({imprv:+,.1f})"
        ax1.text(
            0.02, 0.95, sa_summary,
            transform=ax1.transAxes,
            fontsize=self.theme.legend_font_size,
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor=self.theme.bg_color, edgecolor=self.theme.grid_color, alpha=0.9),
            color=self.theme.text_color
        )

        ax1.set_title("Simulated Annealing: Objective vs Iteration", fontsize=self.theme.title_font_size, color=self.theme.text_color, pad=8)
        ax1.set_ylabel("Objective Value", fontsize=self.theme.label_font_size, color=self.theme.text_color)
        ax1.legend(fontsize=self.theme.legend_font_size, loc="lower right", facecolor=self.theme.bg_color, edgecolor=self.theme.grid_color)

        prob_iters = list(range(len(probs)))
        prob_marker, prob_msize = _get_marker_config(len(probs))
        ax2.plot(
            prob_iters,
            probs,
            color=self.theme.secondary_line_color,
            linewidth=self.theme.line_width,
            marker=prob_marker,
            markersize=prob_msize,
            label=r"Acceptance Prob ($e^{\Delta E / T}$)"
        )
        ax2.axhline(1.0, color="gray", linestyle=":", alpha=0.5, label="Upper Bound (P=1.0)")

        stuck_sub = ""
        if stuck_metrics:
            eps = stuck_metrics.get("stuck_episodes", 0)
            rej = stuck_metrics.get("rejected_moves", 0)
            rate = stuck_metrics.get("rejection_rate", 0.0)
            stuck_sub = f" [Stuck: {eps}x | {rej} rej ({rate}%)]"

        ax2.set_title(r"Simulated Annealing: $e^{\Delta E / T}$ vs Iteration" + stuck_sub, fontsize=self.theme.title_font_size, color=self.theme.text_color, pad=8)
        ax2.set_xlabel("Iteration", fontsize=self.theme.label_font_size, color=self.theme.text_color)
        ax2.set_ylabel(r"$e^{\Delta E / T}$", fontsize=self.theme.label_font_size, color=self.theme.text_color)
        ax2.set_ylim(-0.05, 1.05)
        ax2.legend(fontsize=self.theme.legend_font_size, loc="lower right", facecolor=self.theme.bg_color, edgecolor=self.theme.grid_color)


class RandomRestartPlotTemplate(BasePlotTemplate):

    def create_figure(self, plt) -> Any:
        fig, ax = plt.subplots(figsize=(8.0, 5.0), dpi=self.theme.figure_dpi)
        self.axes = [ax]
        self.apply_theme_to_axis(ax)
        return fig

    def draw_content(self, plt, data: Any) -> None:
        ax = self.axes[0]
        objs = data.get("current", data.get("objectives", [])) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        iters = data.get("iteration", list(range(len(objs)))) if isinstance(data, dict) else list(range(len(objs)))
        run_iterations = data.get("run_iterations", []) if isinstance(data, dict) else []
        n_points = len(objs)
        if n_points == 0:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", color=self.theme.text_color)
            return

        marker, m_size = _get_marker_config(n_points)
        ax.plot(
            iters,
            objs,
            color=self.theme.primary_line_color,
            linewidth=self.theme.line_width,
            marker=marker,
            markersize=m_size,
            label="Current Fitness"
        )

        ax.scatter([iters[0]], [objs[0]], color=self.theme.start_marker_color, s=35, zorder=4, label=f"Initial: {objs[0]:,.1f}")

        best_idx, best_val = max(enumerate(objs), key=lambda x: x[1])
        best_iter = iters[best_idx]
        ax.scatter(
            [best_iter],
            [best_val],
            color=self.theme.best_marker_color,
            s=55,
            zorder=5,
            label=f"Best: {best_val:,.1f} (iter {best_iter})"
        )

        total = 0
        for run, steps in enumerate(run_iterations):
            middle = total + steps / 2
            ax.text(
                middle, 0.975, f"Run {run}: {steps} iterations",
                transform=ax.get_xaxis_transform(),
                ha="center", va="top",
                fontsize=max(7, self.theme.legend_font_size - 1),
                color=self.theme.text_color
            )
            total += steps
            if run < len(run_iterations) - 1:
                ax.axvline(total, linestyle=":", color=self.theme.text_color, alpha=0.5)

        imprv = best_val - objs[0]
        restarts_count = max(0, len(run_iterations) - 1)
        summary_txt = f"Total Iter: {iters[-1] if iters else 0}\nRestarts: {restarts_count}\nInitial: {objs[0]:,.1f}\nBest: {best_val:,.1f}\nImprovement: {imprv:+,.1f}"
        ax.text(
            0.02, 0.96, summary_txt,
            transform=ax.transAxes,
            fontsize=self.theme.legend_font_size,
            verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=self.theme.bg_color, edgecolor=self.theme.grid_color, alpha=0.9),
            color=self.theme.text_color
        )

        ax.set_title("Random Restart Hill Climbing: Objective vs Iteration", fontsize=self.theme.title_font_size, color=self.theme.text_color, pad=10)
        ax.set_xlabel("Total Iterations", fontsize=self.theme.label_font_size, color=self.theme.text_color)
        ax.set_ylabel("Objective Function", fontsize=self.theme.label_font_size, color=self.theme.text_color)
        ax.legend(fontsize=self.theme.legend_font_size, loc="lower right", facecolor=self.theme.bg_color, edgecolor=self.theme.grid_color)


class GeneticAlgorithmPlotTemplate(BasePlotTemplate):

    def create_figure(self, plt) -> Any:
        fig, ax = plt.subplots(figsize=(7.5, 4.8), dpi=self.theme.figure_dpi)
        self.axes = [ax]
        self.apply_theme_to_axis(ax)
        return fig

    def draw_content(self, plt, data: Any) -> None:
        ax = self.axes[0]
        max_vals = data.get("maximum", [])
        mean_vals = data.get("mean", [])
        best_feas = data.get("best_feasible", [])
        n_points = max(len(max_vals), len(mean_vals), len(best_feas))
        if n_points == 0:
            ax.text(0.5, 0.5, "No data available", ha="center", va="center", color=self.theme.text_color)
            return

        marker, m_size = _get_marker_config(n_points)
        if max_vals:
            ax.plot(range(len(max_vals)), max_vals, color=self.theme.primary_line_color, linewidth=self.theme.line_width, marker=marker, markersize=m_size, label="Maximum Fitness")
        if mean_vals:
            ax.plot(range(len(mean_vals)), mean_vals, color=self.theme.secondary_line_color, linewidth=self.theme.line_width, marker=marker, markersize=m_size, label="Mean Fitness")
        if best_feas:
            ax.plot(range(len(best_feas)), best_feas, color=self.theme.best_marker_color, linewidth=self.theme.line_width, linestyle="--", label="Best Feasible")

        ax.set_title("Genetic Algorithm: Fitness vs Generation", fontsize=self.theme.title_font_size, color=self.theme.text_color, pad=10)
        ax.set_xlabel("Generation", fontsize=self.theme.label_font_size, color=self.theme.text_color)
        ax.set_ylabel("Fitness", fontsize=self.theme.label_font_size, color=self.theme.text_color)
        ax.legend(fontsize=self.theme.legend_font_size, loc="lower right", facecolor=self.theme.bg_color, edgecolor=self.theme.grid_color)


class PlotTemplateFactory:

    @staticmethod
    def get_template(data: Any, theme: Optional[str] = None, export_path: Optional[str] = None) -> BasePlotTemplate:
        if isinstance(data, dict):
            if "run_iterations" in data:
                return RandomRestartPlotTemplate(theme=theme, export_path=export_path)
            if "probabilities" in data:
                return SimulatedAnnealingPlotTemplate(theme=theme, export_path=export_path)
            if "maximum" in data:
                return GeneticAlgorithmPlotTemplate(theme=theme, export_path=export_path)
        return SingleMetricPlotTemplate(theme=theme, export_path=export_path)


def show_plot(data: Union[dict, list], theme: Optional[str] = "academic", export_path: Optional[str] = None) -> None:
    template = PlotTemplateFactory.get_template(data, theme=theme, export_path=export_path)
    template.render(data, show=True)


def launch_plot_subprocess(data: Union[dict, list], theme: Optional[str] = "academic", export_path: Optional[str] = None) -> None:
    if not data:
        print("[WARNING] No history data to plot.")
        return

    try:
        script_path = os.path.abspath(__file__)
        payload = {
            "data": data if isinstance(data, dict) else list(data),
            "theme": theme,
            "export_path": export_path
        }
        proc = subprocess.Popen(
            [sys.executable, script_path],
            stdin=subprocess.PIPE,
            text=True
        )
        proc.stdin.write(json.dumps(payload, ensure_ascii=False))
        proc.stdin.close()
    except Exception as e:
        print(f"[ERROR] Failed to launch plot subprocess: {e}")


if __name__ == "__main__":
    try:
        raw_input = sys.stdin.read()
        if raw_input.strip():
            parsed = json.loads(raw_input)
            if isinstance(parsed, dict) and "data" in parsed and ("theme" in parsed or "export_path" in parsed):
                show_plot(parsed["data"], theme=parsed.get("theme", "academic"), export_path=parsed.get("export_path"))
            else:
                show_plot(parsed)
    except Exception as e:
        print(f"[ERROR] Plotter script error: {e}")
