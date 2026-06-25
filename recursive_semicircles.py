import math
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import MaxNLocator

# ----------------------------------------------------------------------
# Settings -- tweak these freely
# ----------------------------------------------------------------------

TOTAL_STEPS = 100        # how many arcs to draw in total
FRAMES_PER_ARC = 18     # base frames for drawing one arc (used at step 1, slowest)
HOLD_FRAMES = 12        # base pause (in frames) after each arc completes (step 1)
FPS = 30
MIN_SPEED_FACTOR = 0.15  # by the last arc, frames/hold shrink to this fraction
                          # of the base values (lower = faster finish). Must be > 0.



# ----------------------------------------------------------------------
# 1. Build the sequence of events using the confirmed rule
# ----------------------------------------------------------------------

def build_events(total_steps):
    """
    Returns a list of dicts: {"from": x0, "to": x1, "upward": bool}
    Each event's "from" equals the previous event's "to" (continuous path).
    """
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


# ----------------------------------------------------------------------
# 2. Geometry helper -- sample points on the correct semicircle
# ----------------------------------------------------------------------

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


# ----------------------------------------------------------------------
# 3. Precompute everything the animation will need
# ----------------------------------------------------------------------

events = build_events(TOTAL_STEPS)

# Vertical bulge alternates globally, one single counter across every step
# regardless of color: step 1 up, step 2 down, step 3 up, step 4 down, ...
# Color (blue/red) stays tied to direction (forward/backward) independently.
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
    """
    Returns a multiplier in (min_factor, 1.0] for how long step `step_index`
    (0-based) should take relative to the base FRAMES_PER_ARC/HOLD_FRAMES.

    1.0  = full length (slowest, used at step 0)
    min_factor = shortest length (fastest, used at the final step)

    Uses an ease-in curve (quadratic) so the speed-up is gentle at first
    and accelerates more noticeably toward the end, rather than ramping
    linearly the whole way.
    """
    if total_steps <= 1:
        return 1.0
    t = step_index / (total_steps - 1)   # 0.0 .. 1.0 across the whole sequence
    eased = t * t                         # quadratic ease-in: starts slow, speeds up
    return 1.0 - eased * (1.0 - min_factor)


# Build the timeline using a PER-STEP frame count: early arcs get the full
# FRAMES_PER_ARC/HOLD_FRAMES, later arcs get progressively fewer frames
# (faster), down to MIN_SPEED_FACTOR of the original at the last step.
timeline = []  # (event_index, fraction_complete)
for i in range(len(events)):
    factor = speed_factor(i, len(events))
    frames_this_arc = max(2, round(FRAMES_PER_ARC * factor))
    hold_this_arc = max(0, round(HOLD_FRAMES * factor))
    for f in range(1, frames_this_arc + 1):
        timeline.append((i, f / frames_this_arc))
    for _ in range(hold_this_arc):
        timeline.append((i, 1.0))


# ----------------------------------------------------------------------
# 4. Set up the popup figure
# ----------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(11, 4.4))
fig.canvas.manager.set_window_title("Recursive semicircle sequence")
fig.patch.set_facecolor("white")


def get_partial_segment(seg, frac):
    n_pts = max(2, int(len(seg) * frac))
    return seg[:n_pts]


def render_frame(idx):
    ax.clear()
    ev_idx, frac = timeline[idx]

    # fully completed arcs so far, colored by direction
    for j in range(ev_idx):
        xs = [p[0] for p in segment_points[j]]
        ys = [p[1] for p in segment_points[j]]
        color = "#1f5fd1" if events[j]["upward"] else "#d11f1f"
        ax.plot(xs, ys, color=color, linewidth=1.5, zorder=2)

    # currently drawing arc, in its direction's color (slightly thicker)
    partial = get_partial_segment(segment_points[ev_idx], frac)
    xs = [p[0] for p in partial]
    ys = [p[1] for p in partial]
    cur_color = "#1f5fd1" if events[ev_idx]["upward"] else "#d11f1f"
    ax.plot(xs, ys, color=cur_color, linewidth=2.2, zorder=3)

    # zoom bounds blend smoothly toward this step's cumulative extent
    prev_lo, prev_hi = cumulative_bounds[ev_idx - 1] if ev_idx > 0 else (0.0, 1.0)
    target_lo, target_hi = cumulative_bounds[ev_idx]
    view_lo = prev_lo + (target_lo - prev_lo) * frac
    view_hi = prev_hi + (target_hi - prev_hi) * frac
    margin = 0.7
    ax.set_xlim(view_lo - margin, view_hi + margin)

    # node DOTS: every visited node always gets a dot, regardless of zoom
    revealed = {0.0}
    for j in range(ev_idx):
        revealed.add(events[j]["from"])
        revealed.add(events[j]["to"])
    revealed.add(events[ev_idx]["from"])
    if frac >= 0.999:
        revealed.add(events[ev_idx]["to"])

    for n in sorted(revealed):
        ax.plot(n, 0, "o", color="black", markersize=4, zorder=4)

    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.spines["bottom"].set_visible(True)
    ax.set_aspect("equal")
    ax.set_facecolor("white")

    # axis TICK LABELS: adaptive "nice number" ticks based on the visible
    # range (1,2,5,10,20,50,100,...), independent of which nodes exist.
    # This is what thins out as the view zooms out, instead of every
    # single visited node's label competing for space.
    ax.xaxis.set_major_locator(MaxNLocator(nbins=10, steps=[1, 2, 5, 10]))
    ax.spines["bottom"].set_position(("data", 0))   # spine sits exactly on y=0
    ax.spines["bottom"].set_color("black")
    ax.spines["bottom"].set_linewidth(1.0)
    ax.xaxis.set_ticks_position("bottom")
    ax.tick_params(axis="x", which="major", length=5, labelsize=11,
                    labelfontfamily="serif", colors="black", pad=8)

    fig.tight_layout()


if __name__ == "__main__":
    # print("Node sequence:", [round(n, 2) for n in [0] + [e["to"] for e in events]])

    anim = FuncAnimation(
        fig, render_frame, frames=len(timeline),
        interval=1000 / FPS, repeat=True
    )

    plt.show()