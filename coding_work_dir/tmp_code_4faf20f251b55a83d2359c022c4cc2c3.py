
import numpy as np

Vmax = 0.0429
S = 72.3
Km = 0.052

reaction_velocity = (Vmax * S) / (Km + S)
print(f"{reaction_velocity:.4f}")
