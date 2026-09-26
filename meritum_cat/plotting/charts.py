"""
Figuras científicas de Meritum_CAT.

Todas las funciones reciben una :class:`matplotlib.figure.Figure` (que limpian y
redibujan) y una función de traducción ``tr(clave, **kw)``, de modo que títulos,
ejes y leyendas aparecen en el idioma activo. Se usa la API orientada a objetos
de matplotlib (sin ``pyplot``), apta para incrustar en la interfaz y para
exportar a PNG/PDF.

Convenciones visuales: una sola escala por eje (nunca doble eje Y), colores
categóricos en orden fijo, cuadrícula fina y discreta, leyenda cuando hay dos o
más series y textos en tinta neutra.
"""
from __future__ import annotations

from typing import Any, Callable

import numpy as np
from matplotlib.figure import Figure

from meritum_cat.core.irt.models import probability_3pl
from meritum_cat.core.irt.information import item_information

Translate = Callable[..., str]

# Paleta categórica en orden fijo (validada para daltonismo en pares adyacentes).
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BAND = "#cde2fb"  # paso claro de la rampa azul para bandas de confianza

THETA_GRID = np.linspace(-4.0, 4.0, 401)


def new_figure(width: float = 9.0, height: float = 5.5, dpi: int = 100) -> Figure:
    """Crea una figura con el fondo y la tipografía de la aplicación."""
    fig = Figure(figsize=(width, height), dpi=dpi, facecolor=SURFACE)
    return fig


def _prepare(fig: Figure, nrows: int = 1, ncols: int = 1):
    fig.clear()
    fig.set_facecolor(SURFACE)
    axes = fig.subplots(nrows, ncols, squeeze=False)
    for ax in axes.flat:
        _style_ax(ax)
    return axes


def _style_ax(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(BASELINE)
        ax.spines[side].set_linewidth(0.8)
    ax.tick_params(colors=INK_2, labelsize=8.5, length=3, width=0.6)
    ax.grid(True, color=GRID, linewidth=0.6, linestyle="-")
    ax.set_axisbelow(True)
    ax.title.set_color(INK)
    ax.xaxis.label.set_color(INK_2)
    ax.yaxis.label.set_color(INK_2)


def _titles(ax, title: str, xlabel: str, ylabel: str) -> None:
    ax.set_title(title, fontsize=10.5, loc="left", color=INK, pad=8)
    ax.set_xlabel(xlabel, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=9)


def _legend(ax, **kw) -> None:
    leg = ax.legend(fontsize=8, frameon=True, labelcolor=INK_2, facecolor=SURFACE, edgecolor=GRID,
                    framealpha=0.92, **kw)
    leg.get_frame().set_linewidth(0.6)
    return leg


def _finish(fig: Figure, suptitle: str | None = None) -> Figure:
    if suptitle:
        fig.suptitle(suptitle, fontsize=11.5, color=INK, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95) if suptitle else None)
    return fig


def _bars(ax, labels: list[str], values: list[float], color: str) -> None:
    x = np.arange(len(labels))
    vals = [np.nan if v is None else v for v in values]
    ax.bar(x, vals, width=0.7, color=color, edgecolor=SURFACE, linewidth=2)
    ax.set_xticks(x, labels, rotation=0 if max(len(s) for s in labels) < 12 else 15,
                  ha="center" if max(len(s) for s in labels) < 12 else "right")


def _grouped_bars(ax, labels: list[str], series: list[tuple[str, list[float]]]) -> None:
    x = np.arange(len(labels))
    k = len(series)
    width = 0.8 / k
    for j, (name, values) in enumerate(series):
        vals = [np.nan if v is None else v for v in values]
        ax.bar(x - 0.4 + width * (j + 0.5), vals, width=width, color=SERIES[j],
               edgecolor=SURFACE, linewidth=2, label=name)
    ax.set_xticks(x, labels)
    _legend(ax)


def _zero_line(ax) -> None:
    ax.axhline(0.0, color=BASELINE, linewidth=1.0)


# --------------------------------------------------------------------------- IRT

def plot_icc_iic(fig: Figure, curves: list[dict[str, Any]], tr: Translate) -> Figure:
    """
    Curvas características (ICC) e informativas (IIC) de uno o varios ítems.

    ``curves``: lista de dicts con claves ``a``, ``b``, ``c`` y ``label``.
    """
    ax1, ax2 = _prepare(fig, 1, 2)[0]
    for j, cv in enumerate(curves[: len(SERIES)]):
        color = SERIES[j]
        p = probability_3pl(THETA_GRID, cv["a"], cv["b"], cv["c"])
        info = item_information(THETA_GRID, cv["a"], cv["b"], cv["c"])
        ax1.plot(THETA_GRID, p, color=color, linewidth=1.8, label=cv["label"])
        ax2.plot(THETA_GRID, info, color=color, linewidth=1.8, label=cv["label"])
        k = int(np.argmax(info))
        ax2.plot(THETA_GRID[k], info[k], "o", color=color, markersize=6,
                 markeredgecolor=SURFACE, markeredgewidth=1.5)
    ax1.set_ylim(-0.02, 1.02)
    ax2.set_ylim(bottom=0)
    _titles(ax1, tr("plot.icc.title"), tr("plot.theta"), tr("plot.icc.y"))
    _titles(ax2, tr("plot.iic.title"), tr("plot.theta"), tr("plot.iic.y"))
    if len(curves) >= 2:
        _legend(ax1, loc="lower right")
        _legend(ax2, loc="upper right")
    return _finish(fig)


def plot_test_information(fig: Figure, a: np.ndarray, b: np.ndarray, c: np.ndarray,
                          tr: Translate, model_label: str = "") -> Figure:
    """Función de información del test (TIF) y función de error estándar, en paneles separados."""
    ax1, ax2 = _prepare(fig, 1, 2)[0]
    if a.size:
        info = item_information(THETA_GRID.reshape(-1, 1), a.reshape(1, -1),
                                b.reshape(1, -1), c.reshape(1, -1)).sum(axis=1)
    else:
        info = np.zeros_like(THETA_GRID)
    with np.errstate(divide="ignore"):
        se = np.where(info > 0, 1.0 / np.sqrt(np.maximum(info, 1e-300)), np.nan)
    ax1.plot(THETA_GRID, info, color=SERIES[0], linewidth=1.8)
    ax2.plot(THETA_GRID, se, color=SERIES[1], linewidth=1.8)
    ax1.set_ylim(bottom=0)
    ax2.set_ylim(0, min(np.nanmax(se) * 1.05 if np.any(np.isfinite(se)) else 1.0, 3.0))
    _titles(ax1, tr("plot.tif.title"), tr("plot.theta"), tr("plot.tif.y"))
    _titles(ax2, tr("plot.sef.title"), tr("plot.theta"), tr("plot.se.y"))
    suffix = f" — {model_label}" if model_label else ""
    return _finish(fig, tr("plot.bank_info.suptitle", n=int(a.size)) + suffix)


# --------------------------------------------------------------------------- CAT

def plot_cat_trace(fig: Figure, theta_history: list[float], se_history: list[float],
                   info_history: list[float], b_selected: list[float],
                   tr: Translate, theta_true: float | None = None,
                   initial_theta: float = 0.0) -> Figure:
    """Trazas de una sesión CAT: theta, error estándar, información acumulada y dificultad."""
    axes = _prepare(fig, 2, 2)
    ax_t, ax_se, ax_i, ax_b = axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]
    k = np.arange(1, len(theta_history) + 1)
    th = np.asarray(theta_history, float)
    se = np.asarray(se_history, float)
    se_plot = np.where(np.isfinite(se), se, np.nan)

    if k.size:
        ax_t.fill_between(k, th - 1.96 * se_plot, th + 1.96 * se_plot, color=BAND,
                          linewidth=0, label=tr("plot.cat.band"))
        ax_t.plot(np.r_[0, k], np.r_[initial_theta, th], color=SERIES[0], linewidth=1.8,
                  marker="o", markersize=4, label=tr("plot.cat.theta_hat"))
        if theta_true is not None:
            ax_t.axhline(theta_true, color=SERIES[1], linewidth=1.5, label=tr("plot.cat.theta_true"))
        _legend(ax_t, loc="best")
        ax_se.plot(k, se_plot, color=SERIES[0], linewidth=1.8, marker="o", markersize=4)
        ax_i.plot(k, info_history, color=SERIES[0], linewidth=1.8, marker="o", markersize=4)
        ax_b.plot(k, b_selected, color=SERIES[0], linewidth=0, marker="o", markersize=6,
                  label=tr("plot.cat.b_selected"))
        ax_b.plot(k, th, color=SERIES[1], linewidth=1.5, label=tr("plot.cat.theta_hat"))
        _legend(ax_b, loc="best")
    ax_se.set_ylim(bottom=0)
    ax_i.set_ylim(bottom=0)
    _titles(ax_t, tr("plot.cat.theta.title"), tr("plot.item_number"), tr("plot.theta"))
    _titles(ax_se, tr("plot.cat.se.title"), tr("plot.item_number"), tr("plot.se.y"))
    _titles(ax_i, tr("plot.cat.info.title"), tr("plot.item_number"), tr("plot.tif.y"))
    _titles(ax_b, tr("plot.cat.b.title"), tr("plot.item_number"), tr("plot.b_axis"))
    for ax in (ax_t, ax_se, ax_i, ax_b):
        ax.xaxis.get_major_locator().set_params(integer=True)
    return _finish(fig)


# --------------------------------------------------------------------------- Monte Carlo

def plot_recovery(fig: Figure, theta_true, theta_est, tr: Translate) -> Figure:
    """Dispersión de habilidad verdadera frente a estimada, con recta identidad."""
    ax = _prepare(fig)[0, 0]
    t = np.asarray(theta_true)
    e = np.asarray(theta_est)
    alpha = 0.55 if t.size <= 2000 else 0.3
    ax.scatter(t, e, s=10, color=SERIES[0], alpha=alpha, linewidths=0, label=tr("plot.examinees"))
    lo = float(min(t.min(), e.min())) - 0.2
    hi = float(max(t.max(), e.max())) + 0.2
    ax.plot([lo, hi], [lo, hi], color=INK_2, linewidth=1.2, label=tr("plot.identity"))
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    _titles(ax, tr("plot.recovery.title"), tr("plot.theta_true"), tr("plot.theta_est"))
    _legend(ax, loc="upper left")
    return _finish(fig)


def plot_error_distribution(fig: Figure, theta_true, theta_est, tr: Translate) -> Figure:
    """Histograma del error de estimación (estimado - verdadero)."""
    ax = _prepare(fig)[0, 0]
    err = np.asarray(theta_est) - np.asarray(theta_true)
    ax.hist(err, bins=40, color=SERIES[0], edgecolor=SURFACE, linewidth=1.0)
    ax.axvline(0.0, color=BASELINE, linewidth=1.0)
    ax.axvline(float(np.mean(err)), color=SERIES[1], linewidth=1.5,
               label=tr("plot.mean_error", v=float(np.mean(err))))
    _titles(ax, tr("plot.error.title"), tr("plot.error.x"), tr("plot.count"))
    _legend(ax, loc="upper right")
    return _finish(fig)


def conditional_stats(theta_true, theta_est, width: float = 0.5, min_n: int = 10):
    """Sesgo y RMSE condicionales por intervalos de theta verdadero."""
    t = np.asarray(theta_true)
    e = np.asarray(theta_est)
    edges = np.arange(-4.0, 4.0 + width, width)
    centers, bias, rmse, counts = [], [], [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (t >= lo) & (t < hi)
        if mask.sum() >= min_n:
            d = e[mask] - t[mask]
            centers.append((lo + hi) / 2)
            bias.append(float(np.mean(d)))
            rmse.append(float(np.sqrt(np.mean(d ** 2))))
            counts.append(int(mask.sum()))
    return np.array(centers), np.array(bias), np.array(rmse), np.array(counts)


def plot_bias_rmse_by_theta(fig: Figure, theta_true, theta_est, tr: Translate) -> Figure:
    """Sesgo y RMSE condicionales a la habilidad verdadera (paneles separados)."""
    ax1, ax2 = _prepare(fig, 1, 2)[0]
    x, bias, rmse, _ = conditional_stats(theta_true, theta_est)
    ax1.plot(x, bias, color=SERIES[0], linewidth=1.8, marker="o", markersize=5)
    _zero_line(ax1)
    ax2.plot(x, rmse, color=SERIES[0], linewidth=1.8, marker="o", markersize=5)
    ax2.set_ylim(bottom=0)
    _titles(ax1, tr("plot.cond_bias.title"), tr("plot.theta_true"), tr("plot.bias.y"))
    _titles(ax2, tr("plot.cond_rmse.title"), tr("plot.theta_true"), tr("plot.rmse.y"))
    return _finish(fig)


def plot_precision_by_items(fig: Figure, k, rmse_k, se_k, tr: Translate) -> Figure:
    """RMSE y error estándar medio en función del número de ítems administrados."""
    ax1, ax2 = _prepare(fig, 1, 2)[0]
    ax1.plot(k, rmse_k, color=SERIES[0], linewidth=1.8, marker="o", markersize=4)
    ax2.plot(k, se_k, color=SERIES[0], linewidth=1.8, marker="o", markersize=4)
    for ax in (ax1, ax2):
        ax.set_ylim(bottom=0)
        ax.xaxis.get_major_locator().set_params(integer=True)
    _titles(ax1, tr("plot.rmse_items.title"), tr("plot.item_number"), tr("plot.rmse.y"))
    _titles(ax2, tr("plot.se_items.title"), tr("plot.item_number"), tr("plot.se.y"))
    return _finish(fig)


def plot_exposure(fig: Figure, exposure_rates, tr: Translate, r_max: float | None = None) -> Figure:
    """Tasas de exposición por ítem (ordenadas) e histograma de exposición."""
    ax1, ax2 = _prepare(fig, 1, 2)[0]
    rates = np.sort(np.asarray(exposure_rates))[::-1]
    x = np.arange(1, rates.size + 1)
    ax1.fill_between(x, 0, rates, color=SERIES[0], step="mid", linewidth=0, alpha=0.9)
    if r_max is not None:
        ax1.axhline(r_max, color=SERIES[1], linewidth=1.5, label=tr("plot.exposure.target", v=r_max))
        _legend(ax1, loc="upper right")
    ax1.set_xlim(0.5, max(1.5, rates.size + 0.5))
    ax1.set_ylim(0, 1.02)
    ax2.hist(rates, bins=np.linspace(0, 1, 21), color=SERIES[0], edgecolor=SURFACE, linewidth=1.0)
    _titles(ax1, tr("plot.exposure.sorted.title"), tr("plot.exposure.rank"), tr("plot.exposure.y"))
    _titles(ax2, tr("plot.exposure.hist.title"), tr("plot.exposure.y"), tr("plot.n_items"))
    return _finish(fig)


def plot_test_length(fig: Figure, lengths, tr: Translate) -> Figure:
    """Distribución de la longitud del test (número de ítems administrados)."""
    ax = _prepare(fig)[0, 0]
    lengths = np.asarray(lengths)
    bins = np.arange(lengths.min() - 0.5, lengths.max() + 1.5, 1.0) if lengths.size else 10
    ax.hist(lengths, bins=bins, color=SERIES[0], edgecolor=SURFACE, linewidth=1.0)
    ax.xaxis.get_major_locator().set_params(integer=True)
    _titles(ax, tr("plot.length.title"), tr("plot.length.x"), tr("plot.count"))
    return _finish(fig)


def plot_cat_vs_fixed(fig: Figure, cat_true, cat_est, fixed_true, fixed_est, tr: Translate) -> Figure:
    """Comparación CAT vs test fijo: RMSE condicional y métricas globales."""
    ax1, ax2 = _prepare(fig, 1, 2)[0]
    for j, (label, t, e) in enumerate(((tr("plot.cat_label"), cat_true, cat_est),
                                       (tr("plot.fixed_label"), fixed_true, fixed_est))):
        x, _, rmse, _ = conditional_stats(t, e)
        ax1.plot(x, rmse, color=SERIES[j], linewidth=1.8, marker="o", markersize=5, label=label)
    ax1.set_ylim(bottom=0)
    _legend(ax1, loc="upper center")

    def glob(t, e):
        d = np.asarray(e) - np.asarray(t)
        return [float(np.sqrt(np.mean(d ** 2))), float(np.mean(np.abs(d)))]

    labels = [tr("metric.rmse"), tr("metric.mae")]
    _grouped_bars(ax2, labels, [(tr("plot.cat_label"), glob(cat_true, cat_est)),
                                (tr("plot.fixed_label"), glob(fixed_true, fixed_est))])
    _titles(ax1, tr("plot.cond_rmse.title"), tr("plot.theta_true"), tr("plot.rmse.y"))
    _titles(ax2, tr("plot.cat_vs_fixed.global"), "", tr("plot.value_theta"))
    return _finish(fig, tr("plot.cat_vs_fixed.suptitle"))


# --------------------------------------------------------------------------- Experiments

def _col(rows, key):
    return [r.get(key) for r in rows]


def plot_experiment(fig: Figure, result, tr: Translate) -> Figure:
    """Figura resumen de un experimento predefinido, según su clave."""
    key = result.key
    rows = result.rows
    col = lambda k: _col(rows, k)  # noqa: E731
    sel_label = lambda v: tr(f"sel.{v}")  # noqa: E731

    if key == "ability_recovery":
        ax1, ax2 = _prepare(fig, 1, 2)[0]
        labels = col("model")
        _grouped_bars(ax1, labels, [(tr("metric.rmse"), col("rmse")), (tr("metric.mae"), col("mae"))])
        _grouped_bars(ax2, labels, [(tr("metric.pearson"), col("pearson")),
                                    (tr("metric.spearman"), col("spearman"))])
        ax2.set_ylim(0, 1.05)
        _titles(ax1, tr("plot.exp.error_by_model"), tr("col.model"), tr("plot.value_theta"))
        _titles(ax2, tr("plot.exp.corr_by_model"), tr("col.model"), tr("plot.correlation"))
    elif key == "estimators":
        ax1, ax2 = _prepare(fig, 1, 2)[0]
        labels = col("estimator")
        _grouped_bars(ax1, labels, [(tr("metric.rmse"), col("rmse")), (tr("metric.mae"), col("mae"))])
        _bars(ax2, labels, col("bias"), SERIES[0])
        _zero_line(ax2)
        _titles(ax1, tr("plot.exp.error_by_estimator"), tr("col.estimator"), tr("plot.value_theta"))
        _titles(ax2, tr("plot.exp.bias_by_estimator"), tr("col.estimator"), tr("plot.bias.y"))
    elif key in ("selection", "exposure"):
        ax1, ax2 = _prepare(fig, 1, 2)[0]
        labels = [sel_label(v) for v in col("selector")]
        _bars(ax1, labels, col("rmse"), SERIES[0])
        _bars(ax2, labels, col("max_exposure"), SERIES[0])
        ax2.set_ylim(0, 1.05)
        _titles(ax1, tr("plot.exp.rmse_by_selector"), "", tr("plot.rmse.y"))
        _titles(ax2, tr("plot.exp.exposure_by_selector"), "", tr("plot.exposure.y"))
    elif key == "cat_vs_fixed":
        ax1, ax2 = _prepare(fig, 1, 2)[0]
        for j, kind in enumerate(("cat", "fixed")):
            sub = [r for r in rows if r["test_type"] == kind]
            label = tr("plot.cat_label") if kind == "cat" else tr("plot.fixed_label")
            ax1.plot(_col(sub, "test_length"), _col(sub, "rmse"), color=SERIES[j], linewidth=1.8,
                     marker="o", markersize=6, label=label)
            ax2.plot(_col(sub, "test_length"), _col(sub, "mean_se"), color=SERIES[j], linewidth=1.8,
                     marker="o", markersize=6, label=label)
        for ax in (ax1, ax2):
            ax.set_ylim(bottom=0)
            _legend(ax)
        _titles(ax1, tr("plot.exp.rmse_by_length"), tr("col.test_length"), tr("plot.rmse.y"))
        _titles(ax2, tr("plot.exp.se_by_length"), tr("col.test_length"), tr("plot.se.y"))
    elif key == "bank_size":
        ax1, ax2 = _prepare(fig, 1, 2)[0]
        x = col("bank_size")
        ax1.plot(x, col("rmse"), color=SERIES[0], linewidth=1.8, marker="o", markersize=6)
        ax2.plot(x, col("max_exposure"), color=SERIES[0], linewidth=1.8, marker="o", markersize=6)
        for ax in (ax1, ax2):
            ax.set_xscale("log")
            ax.set_xticks(x, [str(v) for v in x])
            ax.minorticks_off()
        ax1.set_ylim(bottom=0)
        ax2.set_ylim(0, 1.05)
        _titles(ax1, tr("plot.exp.rmse_by_bank"), tr("col.bank_size"), tr("plot.rmse.y"))
        _titles(ax2, tr("plot.exp.exposure_by_bank"), tr("col.bank_size"), tr("plot.exposure.y"))
    elif key == "test_length":
        ax1, ax2 = _prepare(fig, 1, 2)[0]
        x = col("test_length")
        ax1.plot(x, col("rmse"), color=SERIES[0], linewidth=1.8, marker="o", markersize=6)
        ax2.plot(x, col("mean_se"), color=SERIES[0], linewidth=1.8, marker="o", markersize=6)
        for ax in (ax1, ax2):
            ax.set_ylim(bottom=0)
        _titles(ax1, tr("plot.exp.rmse_by_length"), tr("col.test_length"), tr("plot.rmse.y"))
        _titles(ax2, tr("plot.exp.se_by_length"), tr("col.test_length"), tr("plot.se.y"))
    elif key == "robustness":
        ax1, ax2 = _prepare(fig, 1, 2)[0]
        x = col("param_noise")
        ax1.plot(x, col("rmse"), color=SERIES[0], linewidth=1.8, marker="o", markersize=6)
        ax2.plot(x, col("coverage95"), color=SERIES[0], linewidth=1.8, marker="o", markersize=6)
        ax2.axhline(0.95, color=SERIES[1], linewidth=1.3, label=tr("plot.nominal95"))
        _legend(ax2, loc="lower left")
        ax1.set_ylim(bottom=0)
        ax2.set_ylim(0, 1.02)
        _titles(ax1, tr("plot.exp.rmse_by_noise"), tr("col.param_noise"), tr("plot.rmse.y"))
        _titles(ax2, tr("plot.exp.coverage_by_noise"), tr("col.param_noise"), tr("metric.coverage95"))
    elif key == "populations":
        ax1, ax2 = _prepare(fig, 1, 2)[0]
        labels = col("population")
        _bars(ax1, labels, col("rmse"), SERIES[0])
        _bars(ax2, labels, col("bias"), SERIES[0])
        _zero_line(ax2)
        _titles(ax1, tr("plot.exp.rmse_by_population"), tr("col.population"), tr("plot.rmse.y"))
        _titles(ax2, tr("plot.exp.bias_by_population"), tr("col.population"), tr("plot.bias.y"))
    elif key == "seeds":
        ax = _prepare(fig)[0, 0]
        x = [str(s) for s in col("seed")]
        vals = col("rmse")
        ax.plot(x, vals, color=SERIES[0], linewidth=0, marker="o", markersize=8,
                label=tr("metric.rmse"))
        ax.axhline(float(np.mean(vals)), color=SERIES[1], linewidth=1.3, label=tr("plot.mean"))
        ax.set_ylim(0, max(vals) * 1.3)
        _legend(ax, loc="lower right")
        _titles(ax, tr("plot.exp.rmse_by_seed"), tr("col.seed"), tr("plot.rmse.y"))
    else:  # pragma: no cover
        _prepare(fig)
    return _finish(fig, tr(f"exp.{key}.title"))
