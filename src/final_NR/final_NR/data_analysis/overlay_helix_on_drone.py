#!/usr/bin/env python3
import os
import subprocess
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation

# === Load and prepare data ===
df_log = pd.read_csv('hxx.log')

# Clip time range for true path
start_time = df_log['time'].iloc[0] + 70
end_time = start_time + 30
df_clipped = df_log[(df_log['time'] >= start_time) & (df_log['time'] <= end_time)].reset_index(drop=True)
battery_adj = df_clipped['z'].min() - df_clipped['z_ref'].min()
x = df_clipped['x'].values
y = df_clipped['y'].values
z = (df_clipped['z'] - battery_adj).values

# Clip reference and black dot paths
df_clipped_black_dot = df_log[(df_log['time'] >= start_time - 0.6) & (df_log['time'] <= end_time + 0.6)].reset_index(drop=True)
x_ref_blackdot = df_clipped_black_dot['x_ref'].values
y_ref_blackdot = df_clipped_black_dot['y_ref'].values
z_ref_blackdot = df_clipped_black_dot['z_ref'].values

df_clipped_ref = df_log[(df_log['time'] >= start_time - 0.8) & (df_log['time'] <= start_time + 15 + 0.8)].reset_index(drop=True)
x_ref = df_clipped_ref['x_ref'].values
y_ref = df_clipped_ref['y_ref'].values
z_ref = df_clipped_ref['z_ref'].values

# === Set up 3D figure ===
fig = plt.figure(facecolor='none', figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d', facecolor='none')
ax.set_facecolor('none')
ax.set_axis_off()
ax.xaxis.pane.set_edgecolor('none')
ax.yaxis.pane.set_edgecolor('none')
ax.zaxis.pane.set_edgecolor('none')
ax.xaxis.set_pane_color((1, 1, 1, 0))
ax.yaxis.set_pane_color((1, 1, 1, 0))
ax.zaxis.set_pane_color((1, 1, 1, 0))
ax.set_box_aspect([1, 1, 1])
ax.view_init(elev=23, azim=0)
ax.dist = 14
ax.set_proj_type('persp')

ax.plot3D(-x_ref, y_ref, -z_ref, 'b--', label='Reference')
trace, = ax.plot([], [], [], 'r-', label='Actual')
ref_dot, = ax.plot([], [], [], 'ko', markersize=5, label='Reference Dot')
ax.legend(frameon=False)

# === Animation logic ===
def init():
    trace.set_data(x[:0], y[:0])
    trace.set_3d_properties(-z[:0])
    ref_dot.set_data(np.array([]), np.array([]))
    ref_dot.set_3d_properties(np.array([]))  # <== FIXED
    return trace, ref_dot

def update(frame):
    if frame < len(x_ref_blackdot):
        ref_dot.set_data(np.array([-x_ref_blackdot[frame]]), np.array([y_ref_blackdot[frame]]))
        ref_dot.set_3d_properties(np.array([-z_ref_blackdot[frame]]))
    return trace, ref_dot


# === Calculate FPS for 30 seconds ===
fps = len(x) / 30
interval_ms = 1000 / fps

# === Save transparent PNG frames ===
os.makedirs("frames_overlay", exist_ok=True)
init()
for i in range(len(x)):
    update(i)
    fig.savefig(f"frames_overlay/frame_{i:04d}.png", dpi=200, transparent=True, facecolor='none')

# === Convert to transparent .mov ===
subprocess.run([
    "ffmpeg", "-y",
    "-framerate", str(int(fps)),
    "-i", "frames_overlay/frame_%04d.png",
    "-c:v", "qtrle",
    "-pix_fmt", "argb",
    "trajectory.mov"
])

# === Overlay onto drone video ===
subprocess.run([
    "ffmpeg", "-y",
    "-i", "drone.MOV",
    "-i", "trajectory.mov",
    "-filter_complex", "[0:v][1:v] overlay=shortest=1",
    "-c:a", "copy",
    "output_overlay.mp4"
])
