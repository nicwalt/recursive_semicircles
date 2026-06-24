import matplotlib.pyplot as plt
import numpy as np


def parse_sequence(text: str):
    text = text.strip()
    if not text:
        return []
    parts = text.replace(',', ' ').split()
    values = []
    for part in parts:
        try:
            value = float(part)
        except ValueError:
            raise ValueError(f"Cannot parse {part!r} as a number.")
        if value < 0:
            raise ValueError("All sequence values must be non-negative.")
        values.append(value)
    return values


def draw_semicircles(pause_time=0.008, steps=120):
    def tick_step_for_width(width):
        if width <= 10:
            return 1
        if width <= 30:
            return 5
        if width <= 100:
            return 10
        if width <= 300:
            return 20
        return 100

    plt.ion()
    fig, ax = plt.subplots()
    ax.set_xlabel('x')
    ax.set_ylabel('')
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_position('zero')
    ax.spines['bottom'].set_color('black')
    ax.spines['bottom'].set_linewidth(1.0)
    ax.set_title('Semicircles on the positive x axis')

    full_x_min = 0
    full_x_max = 1000
    view_left = 1.0
    view_right = 5.0
    ax.set_xbound(full_x_min, full_x_max)
    ax.set_xlim(view_left, view_right)
    ax.set_ylim(0, 5)

    visited = {0.0}
    x_current = 0.0
    jump = 1
    max_radius = 1

    while True:
        forward = x_current + jump
        backward = x_current - jump

        if backward >= 0 and backward not in visited:
            next_x = backward
        else:
            next_x = forward

        if next_x in visited or next_x < 0:
            offset = 1
            while True:
                candidate_backward = x_current - jump - offset
                candidate_forward = x_current + jump + offset
                if candidate_backward >= 0 and candidate_backward not in visited:
                    next_x = candidate_backward
                    break
                if candidate_forward not in visited:
                    next_x = candidate_forward
                    break
                offset += 1

        visited.add(next_x)
        diameter = abs(next_x - x_current)
        radius = diameter / 2.0
        if radius == 0:
            jump += 1
            continue

        center = min(x_current, next_x) + radius
        max_radius = max(max_radius, radius)
        theta = np.linspace(np.pi, 0, steps)
        x = center + radius * np.cos(theta)
        y = radius * np.sin(theta)
        line, = ax.plot([], [], color='blue')

        if max(x) + 50 > full_x_max:
            full_x_max = int(np.ceil(max(x) + 50))
            ax.set_xbound(full_x_min, full_x_max)

        for i in range(1, len(x) + 1):
            line.set_data(x[:i], y[:i])
            current_x_pos = x[i - 1]
            required_right = current_x_pos + 0.5
            if required_right > view_right:
                view_right += (required_right - view_right) * 0.06

            if view_right - view_left > 5.0 and view_left > 0.0:
                view_left -= min(0.02, view_left)

            view_left = max(full_x_min, view_left)
            view_right = min(full_x_max, view_right)

            window_width = view_right - view_left
            step = tick_step_for_width(window_width)
            start_tick = np.floor(view_left / step) * step
            end_tick = np.ceil(view_right / step) * step
            ax.set_xlim(view_left, view_right)
            ax.set_xticks(np.arange(start_tick, end_tick + 1e-8, step))
            ax.set_ylim(0, max_radius * 1.2)
            fig.canvas.draw()
            plt.pause(pause_time)

        x_current = next_x
        jump += 1


if __name__ == '__main__':
    draw_semicircles()
