from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "figures"
PNG = OUT_DIR / "Figure1_WRR.png"
PDF = OUT_DIR / "Figure1_WRR.pdf"

COLORS = {
    "input": "#DCEAF7",
    "prep": "#EDF1F5",
    "analysis": "#F6E7C9",
    "output": "#E3EBD8",
    "border": "#8B96A1",
    "header": "#33404D",
    "text": "#26303A",
    "muted": "#5F6B76",
    "arrow": "#66717C",
    "arrow2": "#A4ADB6",
}


def box(ax, x, y, w, h, txt, fc, fs=11.7, fw="normal", ha="center", lw=1.25):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.035,rounding_size=0.09",
        facecolor=fc,
        edgecolor=COLORS["border"],
        linewidth=lw,
    )
    ax.add_patch(patch)
    tx = x + (w / 2 if ha == "center" else 0.18)
    ax.text(
        tx,
        y + h / 2,
        txt,
        ha=ha,
        va="center",
        fontsize=fs,
        fontweight=fw,
        color=COLORS["text"],
        linespacing=1.28,
    )
    return patch


def box_rich(
    ax,
    x,
    y,
    w,
    h,
    title,
    body,
    fc,
    title_fs=11.6,
    body_fs=10.8,
    lw=1.25,
    body_bbox=None,
):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.04,rounding_size=0.09",
        facecolor=fc,
        edgecolor=COLORS["border"],
        linewidth=lw,
    )
    ax.add_patch(patch)
    cx = x + w / 2
    ax.text(
        cx,
        y + h * 0.62,
        title,
        ha="center",
        va="center",
        fontsize=title_fs,
        fontweight="semibold",
        color=COLORS["text"],
    )
    ax.text(
        cx,
        y + h * 0.34,
        body,
        ha="center",
        va="center",
        fontsize=body_fs,
        fontweight="normal",
        color=COLORS["text"],
        linespacing=1.22,
        bbox=body_bbox,
    )
    return patch


def header(ax, x0, x1, txt):
    ax.text(
        (x0 + x1) / 2,
        8.6,
        txt,
        ha="center",
        va="bottom",
        fontsize=14.5,
        fontweight="semibold",
        color=COLORS["header"],
    )
    ax.plot([x0, x1], [8.34, 8.34], color=COLORS["border"], lw=1.0)


def arrow(ax, a, b, lw=2.0, color=None, cs="arc3,rad=0.0", ms=16, style="-|>"):
    arr = FancyArrowPatch(
        a,
        b,
        arrowstyle=style,
        mutation_scale=ms,
        linewidth=lw,
        color=color or COLORS["arrow"],
        connectionstyle=cs,
        shrinkA=6,
        shrinkB=6,
    )
    ax.add_patch(arr)
    return arr


def build_figure():
    fig, ax = plt.subplots(figsize=(18.8, 9.8))
    fig.patch.set_facecolor("white")
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 9)
    ax.axis("off")

    header(ax, 0.4, 3.6, "Input")
    header(ax, 4.0, 10.4, "Processing")
    header(ax, 10.8, 17.6, "Output")

    box_rich(ax, 0.40, 6.38, 2.72, 1.08, "Precipitation data", "ASOS hourly to daily totals", COLORS["input"], title_fs=12.2, body_fs=11.1)
    box_rich(ax, 0.40, 4.93, 2.72, 1.08, "Attention data", "Naver, Google, news volume", COLORS["input"], title_fs=12.2, body_fs=11.1)
    box_rich(ax, 0.40, 3.36, 2.72, 1.20, "Civil complaint data", "date, region, complaint text", COLORS["input"], title_fs=12.1, body_fs=11.0)
    box_rich(ax, 0.40, 1.88, 2.72, 1.10, "Spatial support", "administrative boundaries,\npopulation", COLORS["input"], title_fs=12.0, body_fs=10.8)

    box_rich(ax, 3.78, 6.05, 3.18, 1.58, "Event definition", "2022 and 2023 flood windows\nordinary-week baseline blocks", COLORS["prep"], title_fs=12.0, body_fs=10.9)
    box_rich(ax, 3.78, 4.18, 3.18, 1.58, "Complaint preprocessing", "keyword filtering\nmanual validation", COLORS["prep"], title_fs=12.0, body_fs=10.9)
    box_rich(ax, 3.78, 2.31, 3.18, 1.58, "Complaint enrichment", "emotion classification\ngrouped emotion categories", COLORS["prep"], title_fs=12.0, body_fs=10.9)

    box_rich(ax, 7.42, 4.15, 2.72, 2.28, "Integrated analysis table", "daily aggregation\nweekly aggregation\nregional harmonization", COLORS["prep"], title_fs=12.2, body_fs=11.1)

    box_rich(
        ax,
        10.90,
        6.15,
        3.12,
        1.12,
        "RQ1 Temporal synchronization",
        "lag correlations and block bootstrap",
        COLORS["analysis"],
        title_fs=11.6,
        body_fs=10.8,
        body_bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.58, "pad": 0.55},
    )
    box_rich(ax, 10.90, 4.70, 3.12, 1.12, "RQ2 Emotional composition", "baseline-referenced bootstrap", COLORS["analysis"], title_fs=11.6, body_fs=10.8)
    box_rich(ax, 10.90, 3.25, 3.12, 1.12, "RQ3 Spatial response", "regional alignment and Moran's I", COLORS["analysis"], title_fs=11.6, body_fs=10.8)
    box_rich(ax, 10.90, 1.52, 3.12, 1.34, "Validation and robustness", "grouped emotions\nalternative specs\npopulation normalization", COLORS["analysis"], title_fs=11.2, body_fs=10.5)

    box_rich(ax, 14.72, 6.18, 2.45, 0.98, "Figures 2-3", "context patterns", COLORS["output"], title_fs=11.8, body_fs=11.0)
    box_rich(ax, 14.72, 4.73, 2.45, 0.98, "Figure 4", "temporal lagged response", COLORS["output"], title_fs=11.8, body_fs=11.0)
    box_rich(ax, 14.72, 3.28, 2.45, 0.98, "Figure 5", "event-dependent\nemotional shifts", COLORS["output"], title_fs=11.5, body_fs=10.7)
    box_rich(ax, 14.72, 1.83, 2.45, 0.98, "Figures 6-7", "spatial coupling and\nnegative-emotion clusters", COLORS["output"], title_fs=11.3, body_fs=10.5)
    box_rich(ax, 14.72, 0.34, 2.45, 1.16, "Core interpretation", "institutionalized civic\nresponse under floods", COLORS["output"], title_fs=11.3, body_fs=10.5)

    for y_in, y_out in [(6.92, 6.84), (5.47, 4.99), (3.96, 4.99), (2.43, 3.13)]:
        arrow(ax, (3.12, y_in), (3.78, y_out), lw=2.2)

    arrow(ax, (6.96, 6.84), (7.42, 5.88), lw=2.0)
    arrow(ax, (6.96, 4.99), (7.42, 5.34), lw=2.0)
    arrow(ax, (6.96, 3.13), (7.42, 4.78), lw=2.0)

    arrow(ax, (10.14, 5.70), (14.72, 6.67), lw=2.0)
    arrow(ax, (10.14, 5.70), (10.90, 6.71), lw=2.0)
    arrow(ax, (10.14, 5.32), (10.90, 5.26), lw=2.0)
    arrow(ax, (10.14, 4.94), (10.90, 3.81), lw=2.0)
    arrow(ax, (10.14, 4.56), (10.90, 2.20), lw=1.8, color=COLORS["arrow2"])

    arrow(ax, (14.02, 6.71), (14.72, 5.22), lw=1.9)
    arrow(ax, (14.02, 5.26), (14.72, 3.77), lw=1.9)
    arrow(ax, (14.02, 3.81), (14.72, 2.32), lw=1.9)
    arrow(ax, (14.02, 2.20), (14.72, 0.93), lw=1.7, color=COLORS["arrow2"])

    for y, rad in zip([6.67, 5.22, 3.77, 2.32], [-0.20, -0.16, -0.12, -0.08]):
        arrow(ax, (17.08, y), (17.06, 0.93), lw=1.6, color=COLORS["arrow2"], cs=f"arc3,rad={rad}")

    ax.text(7.48, 6.76, "Shared preprocessing backbone", fontsize=10.6, color=COLORS["muted"], ha="left")
    ax.text(12.46, 0.92, "Supplementary checks\nsupport RQ2-RQ3 interpretation", fontsize=9.6, color=COLORS["muted"], ha="center")
    return fig


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig = build_figure()
    fig.savefig(PNG, dpi=300, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(PDF, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(PNG)
    print(PDF)


if __name__ == "__main__":
    main()
