import math
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import MaxNLocator, FuncFormatter

TOTAL_STEPS = 100
FRAMES_PER_ARC = 60
HOLD_FRAMES = 60
FPS = 30
MIN_SPEED_FACTOR = 1


def build_events(total_steps):
    events = []
    pos = 0.0
    length = 1
    visited = {0.0}

    for _ in range(total_steps):
        backward_target = pos - length
        forward_target = pos + length

        if backward_target >= 0 and backward_target not in visited:
            nxt = backward_target
            upward = False
        else:
            nxt = forward_target
            upward = True

        events.append({"from": pos, "to": nxt, "upward": upward})
        visited.add(nxt)
        pos = nxt
        length += 1

    return events


def semicircle_arc_points(x0, x1, upward, n=80):
    cx = (x0 + x1) / 2.0
    r = abs(x1 - x0) / 2.0
    if x0 <= x1:
        t0, t1 = math.pi, 0.0
    else:
        t0, t1 = 0.0, math.pi
    sign = 1.0 if upward else -1.0
    pts = []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        x = cx + r * math.cos(t)
        y = sign * r * math.sin(t)
        pts.append((x, y))
    return pts


events = build_events(TOTAL_STEPS)

for i, e in enumerate(events):
    e["bulge_up"] = (i % 2 == 0)

segment_points = [semicircle_arc_points(e["from"], e["to"], e["bulge_up"]) for e in events]

cumulative_bounds = []
lo, hi = 0.0, 1.0
for seg in segment_points:
    xs = [p[0] for p in seg]
    lo = min(lo, min(xs))
    hi = max(hi, max(xs))
    cumulative_bounds.append((lo, hi))


def speed_factor(step_index, total_steps, min_factor=MIN_SPEED_FACTOR):
    if total_steps <= 1:
        return 1.0
    t = step_index / (total_steps - 1)
    eased = t * t
    return 1.0 - eased * (1.0 - min_factor)


timeline = []
for i in range(len(events)):
    factor = speed_factor(i, len(events))
    frames_this_arc = max(2, round(FRAMES_PER_ARC * factor))
    hold_this_arc = max(0, round(HOLD_FRAMES * factor))
    for f in range(1, frames_this_arc + 1):
        timeline.append((i, f / frames_this_arc))
    for _ in range(hold_this_arc):
        timeline.append((i, 1.0))


fig, ax = plt.subplots(figsize=(11, 4.8))
fig.canvas.manager.set_window_title("Recursive semicircle sequence")
fig.patch.set_facecolor("white")
fig.subplots_adjust(bottom=0.12)

paused = False


def toggle_pause(event=None):
    global paused
    paused = not paused


def on_key(event):
    if event.key == " ":
        toggle_pause()


fig.canvas.mpl_connect("key_press_event", on_key)


def get_partial_segment(seg, frac):
    n_pts = max(2, int(len(seg) * frac))
    return seg[:n_pts]


_current_idx = 0


def render_frame(_unused_frame_num):
    global _current_idx

    if paused:
        return

    idx = _current_idx
    _current_idx += 1
    if _current_idx >= len(timeline):
        _current_idx = 0

    ax.clear()
    ev_idx, frac = timeline[idx]

    for j in range(ev_idx):
        xs = [p[0] for p in segment_points[j]]
        ys = [p[1] for p in segment_points[j]]
        color = "#1f5fd1" if events[j]["upward"] else "#d11f1f"
        ax.plot(xs, ys, color=color, linewidth=1.5, zorder=2)

    partial = get_partial_segment(segment_points[ev_idx], frac)
    xs = [p[0] for p in partial]
    ys = [p[1] for p in partial]
    cur_color = "#1f5fd1" if events[ev_idx]["upward"] else "#d11f1f"
    ax.plot(xs, ys, color=cur_color, linewidth=2.2, zorder=3)

    prev_lo, prev_hi = cumulative_bounds[ev_idx - 1] if ev_idx > 0 else (0.0, 1.0)
    target_lo, target_hi = cumulative_bounds[ev_idx]
    view_lo = prev_lo + (target_lo - prev_lo) * frac
    view_hi = prev_hi + (target_hi - prev_hi) * frac
    margin = 0.7
    left_edge = view_lo - margin
    ax.set_xlim(left_edge, view_hi + margin)

    revealed = {0.0}
    for j in range(ev_idx):
        revealed.add(events[j]["from"])
        revealed.add(events[j]["to"])
    revealed.add(events[ev_idx]["from"])
    if frac >= 0.999:
        revealed.add(events[ev_idx]["to"])

    for n in sorted(revealed):
        ax.plot(n, 0, "o", color="black", markersize=4, zorder=4)

    cur_x, cur_y = partial[-1]
    badge_color = cur_color
    ev = events[ev_idx]
    step_length = ev["to"] - ev["from"]
    if frac >= 0.999:
        badge_text = f"{round(ev['to']):d}"
    else:
        badge_text = f"{'+' if step_length >= 0 else '-'}{abs(round(step_length)):d}"

    all_ys_so_far = [0.0, cur_y]
    for j in range(ev_idx):
        all_ys_so_far.extend(p[1] for p in segment_points[j])
    all_ys_so_far.extend(p[1] for p in partial)
    max_y_so_far = max(all_ys_so_far)
    min_y_so_far = min(all_ys_so_far)
    badge_y = max_y_so_far + 1.2

    ax.plot([cur_x, cur_x], [cur_y, badge_y - 0.4], color=badge_color,
            linewidth=0.7, linestyle=(0, (3, 2)), zorder=5)
    ax.plot(cur_x, cur_y, "o", color=badge_color, markersize=5, zorder=6)
    ax.annotate(
        badge_text, (cur_x, badge_y),
        ha="center", va="center", fontsize=12, family="serif",
        fontweight="medium", color=badge_color, zorder=7,
        bbox=dict(boxstyle="round,pad=0.32", facecolor=("#E6F1FB" if events[ev_idx]["upward"] else "#FCEBEB"),
                   edgecolor=badge_color, linewidth=0.8),
    )

    ax.set_ylim(min_y_so_far - 0.6, badge_y + 0.9)

    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["bottom"].set_visible(True)
    ax.set_aspect("equal")
    ax.set_facecolor("white")

    ax.xaxis.set_major_locator(MaxNLocator(nbins=10, steps=[1, 2, 5, 10], integer=True))
    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda val, pos: "" if val < 0 else f"{round(val):d}")
    )
    ax.spines["bottom"].set_position(("data", 0))
    ax.spines["bottom"].set_color("black")
    ax.spines["bottom"].set_linewidth(1.0)
    ax.xaxis.set_ticks_position("bottom")
    ax.tick_params(axis="x", which="major", length=5, labelsize=11,
                    labelfontfamily="serif", colors="black", pad=8)

    if hasattr(fig, "_step_text") and fig._step_text is not None:
        fig._step_text.remove()
    fig._step_text = fig.text(0.02, 0.02, f"Step {ev_idx + 1}", fontsize=12,
                               family="serif", color="#3d3d3a", ha="left", va="bottom")


if __name__ == "__main__":
    # print("Node sequence:", [round(n, 2) for n in [0] + [e["to"] for e in events]])
    # print("Press spacebar to pause or resume.")

    anim = FuncAnimation(
        fig, render_frame, interval=1000 / FPS,
        cache_frame_data=False
    )

    plt.show()