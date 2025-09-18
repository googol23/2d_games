import numpy as np
from numba import njit, prange

@njit(parallel=True)
def compute_gaussians(X, Y, centers, sigmas, amplitudes):
    Z = np.zeros_like(X)
    n_peaks = centers.shape[0]
    for i in prange(n_peaks):  # parallel loop
        cx, cy = centers[i]
        sigma_x, sigma_y = sigmas[i]
        amp = amplitudes[i]
        for j in range(X.shape[0]):
            for k in range(X.shape[1]):
                Z[j, k] += amp * np.exp(-(((X[j,k]-cx)**2)/(2*sigma_x**2) + ((Y[j,k]-cy)**2)/(2*sigma_y**2)))
    return Z

def generate_topological_map(width, height, n_of_peaks=5, seed=None) -> np.ndarray:
    if seed is not None:
        np.random.seed(seed)

    x = np.linspace(0, 1, width, dtype=np.float32)
    y = np.linspace(0, 1, height, dtype=np.float32)
    X, Y = np.meshgrid(x, y)

    centers = np.random.rand(n_of_peaks, 2).astype(np.float32)
    sigmas = np.random.uniform(0.05, 0.2, (n_of_peaks, 2)).astype(np.float32)
    amplitudes = np.random.uniform(0, 1, n_of_peaks).astype(np.float32)

    Z = compute_gaussians(X, Y, centers, sigmas, amplitudes)
    return Z

def visualize_topological_map(topology, cmap="terrain", debug_name=None, show=False):
    """
    Efficiently visualize a 2D numpy array Z as a terrain map.
    """
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6,6), dpi=100)
    ax.imshow(topology, cmap=cmap, interpolation="nearest")
    ax.axis("off")  # remove axes

    if debug_name is not None:
        plt.savefig(f"{debug_name}.png", bbox_inches="tight", pad_inches=0)
    elif not show:
        plt.savefig(f"topological_map.png", bbox_inches="tight", pad_inches=0)

    if show:
        plt.show()

    plt.close(fig)
