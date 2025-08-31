import matplotlib.pyplot as plt
import numpy as np

DEBUG_TOPO=True

def generate_topological_map(width, height, n_of_peaks=5, seed=None, debug_name=None):
    if seed is not None:
        np.random.seed(seed)

    # Grid coordinates
    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    X, Y = np.meshgrid(x, y)

    Z = np.zeros_like(X)

    # Add multiple Gaussians
    for _ in range(n_of_peaks):
        # Random center
        cx, cy = np.random.rand(), np.random.rand()
        # Random sigma (spread)
        sigma_x, sigma_y = np.random.uniform(0.05, 0.2), np.random.uniform(0.05, 0.2)
        # Random amplitude (+ can make mountains, - can make valleys)
        amplitude = np.random.uniform(-1, 1)

        gaussian = amplitude * np.exp(-(((X-cx)**2)/(2*sigma_x**2) + ((Y-cy)**2)/(2*sigma_y**2)))
        Z += gaussian

    # Normalize to [0, 1] for visualization
    Z = (Z - Z.min()) / (Z.max() - Z.min())

    if DEBUG_TOPO is True:
        plt.figure(figsize=(6,6))
        plt.imshow(Z, cmap="terrain")
        plt.gca().set_position([0, 0, 1, 1])
        if debug_name is None:
            plt.savefig("topology_map.png")
        else:
            plt.savefig(f"{debug_name}.png")
        plt.close()
    return Z

if __name__ == "__main__":
    map = generate_topological_map(200, 200, n_of_peaks=10)
