"""
Recursive semicircle sequence on a number line -- live popup animation.

Run this script directly:
    python recursive_semicircles.py

A window will pop up and animate the construction step by step, with the
view zooming out as the path grows. No files are written -- everything
happens in a live matplotlib window.

Rule (confirmed):
    A length counter starts at 1 and increases by one every step: 1, 2, 3, ...
    At each step, from the current position `pos`:
        backward_target = pos - length
        - If backward_target is >= 0 AND has NOT been visited before,
          the path goes BACKWARD to it (arc dips below the axis).
        - Otherwise, the path goes FORWARD to pos + length
          (arc rises above the axis).
    The length counter keeps incrementing regardless of direction taken.

This produces:
    0 -> 1 -> 3 -> 6 -> 2 -> 7 -> 13 -> 20 -> 12 -> 21 -> ...

Color coding:
    Blue semicircle = forward / positive-direction step
    Red semicircle  = backward / negative-direction step

Vertical position alternates globally across every step, regardless of
color: step 1 bulges up, step 2 bulges down, step 3 up, step 4 down, etc.
"""