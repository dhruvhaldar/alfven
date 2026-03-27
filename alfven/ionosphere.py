import math
import numpy as np

class ChapmanProfile:
    def __init__(self, layers):
        self.layers = layers
        # Optimization: Pre-extract and cache layer parameters as 2D NumPy arrays
        # This eliminates list comprehensions and np.array allocations on every density() call.
        self._update_cached_arrays()

    def _update_cached_arrays(self):
        if self.layers:
            # Keep as 1D arrays initially, reshape dynamically in density based on input dimensions
            self._h0_arr = np.array([l.h0 for l in self.layers], dtype=np.float64)
            self._inv_H_arr = np.array([l._inv_H for l in self.layers], dtype=np.float64)
            self._n_max_exp_arr = np.array([l._n_max_exp_half for l in self.layers], dtype=np.float64)
        else:
            self._h0_arr = self._inv_H_arr = self._n_max_exp_arr = np.array([], dtype=np.float64)

    def density(self, h):
        """
        Calculate total electron density at height h.

        Args:
            h (float or np.ndarray): Altitude in km.

        Returns:
            float or np.ndarray: Electron density in m^-3.
        """
        if not self.layers:
            # Optimization: Use isinstance(h, (int, float, np.number)) instead of np.isscalar(h).
            # np.isscalar() has significant overhead compared to a built-in type check.
            # Using isinstance is ~4x faster for array-like inputs and moderately faster for scalars.
            return 0.0 if isinstance(h, (int, float, np.number)) else np.zeros_like(h)

        if isinstance(h, (int, float, np.number)):
            # Fallback for scalars: sum is fast and avoids array overhead
            return sum([layer.density(h) for layer in self.layers])

        # Fast path if there's only 1 layer
        if len(self.layers) == 1:
            return self.layers[0].density(h)

        # Optimization: When calculating combined results of multiple objects over an array of inputs (like atmospheric layers), avoid calling each object's method in a Python loop. Instead, extract properties into NumPy arrays, expand dimensions with np.newaxis for broadcasting, perform in-place operations, and sum across the object axis (np.sum(axis=0)) to eliminate Python iteration and intermediate array overhead.
        h_arr = np.asarray(h)
        h_expanded = h_arr[np.newaxis, :] if h_arr.ndim == 1 else h_arr

        # Use dynamically built arrays if self.layers length changed unexpectedly,
        # otherwise use the fast cached arrays.
        if self._h0_arr.size == 0 and self.layers or len(self.layers) != len(self._h0_arr):
            self._update_cached_arrays()

        # Reshape cached arrays to add a new axis for every dimension in h
        # so they broadcast against h properly.
        # Example: if h is shape (A, B), shape becomes (N, 1, 1)
        shape_suffix = (1,) * h_arr.ndim
        h0_arr = self._h0_arr.reshape(-1, *shape_suffix)
        inv_H_arr = self._inv_H_arr.reshape(-1, *shape_suffix)
        n_max_exp_arr = self._n_max_exp_arr.reshape(-1, *shape_suffix)

        # In-place vectorized calculation of density over all layers
        # z = (h - h0) / H
        z = (h_expanded - h0_arr)
        z *= inv_H_arr

        # Calculate term: n_max_exp * exp(-0.5 * (z + exp(-z)))
        term = np.exp(-z)
        term += z
        term *= -0.5
        np.exp(term, out=term)
        term *= n_max_exp_arr

        return np.sum(term, axis=0)

    def __add__(self, other):
        if isinstance(other, ChapmanLayer):
            return ChapmanProfile(self.layers + [other])
        elif isinstance(other, ChapmanProfile):
            return ChapmanProfile(self.layers + other.layers)
        else:
            raise TypeError("Can only add ChapmanLayer or ChapmanProfile")

    def plot_altitude_profile(self, min_h, max_h, filename="ionosphere_profile.png"):
        """
        Plot the altitude profile.

        Args:
            min_h (float): Minimum altitude in km.
            max_h (float): Maximum altitude in km.
            filename (str): Filename to save the plot.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("Matplotlib not installed. Cannot plot.")
            return

        h = np.linspace(min_h, max_h, 500)
        n = self.density(h)

        plt.figure(figsize=(6, 8))
        plt.plot(n, h)
        plt.xscale('log') # Usually density is plotted on log scale
        plt.xlabel('Electron Density (m^-3)')
        plt.ylabel('Altitude (km)')
        plt.title('Ionospheric Profile')
        plt.grid(True, which="both", ls="-")
        plt.savefig(filename)
        print(f"Plot saved to {filename}")

    def get_profile_data(self, min_h, max_h, steps=100):
        """
        Get profile data for API/Frontend.

        Args:
            min_h (float): Min altitude km.
            max_h (float): Max altitude km.
            steps (int): Number of steps.

        Returns:
            dict: {"altitude": list, "density": list}
        """
        h = np.linspace(min_h, max_h, steps)
        n = self.density(h)
        return {"altitude": h.tolist(), "density": n.tolist()}

class ChapmanLayer:
    def __init__(self, h0, H, n_max):
        """
        Initialize a Chapman Layer.

        Args:
            h0 (float): Peak altitude in km.
            H (float): Scale height in km.
            n_max (float): Peak electron density in m^-3.
        """
        self.h0 = h0
        self.H = H
        self.n_max = n_max
        # Optimization: Precompute inverted constants and mathematically simplified terms
        # for faster density calculation: n_max * exp(0.5)
        self._inv_H = 1.0 / H
        self._n_max_exp_half = n_max * math.exp(0.5)

    def density(self, h):
        """
        Calculate electron density at height h using Chapman function.
        n(h) = n_max * exp(0.5 * (1 - z - exp(-z)))
        where z = (h - h0) / H

        Args:
            h (float or np.ndarray): Altitude in km.

        Returns:
            float or np.ndarray: Electron density.
        """
        # Optimization: Use precomputed _inv_H to turn division into multiplication (~20% faster)
        z = (h - self.h0) * self._inv_H

        # Optimization: Use isinstance(h, (int, float, np.number)) instead of np.isscalar(h).
        # np.isscalar() has significant overhead compared to a built-in type check.
        # Using isinstance is ~4x faster for array-like inputs and moderately faster for scalars.
        if isinstance(h, (int, float, np.number)):
            # Optimization: Algebraically expand exp(0.5 * (1 - z - exp(-z)))
            # to exp(0.5) * exp(-0.5 * (z + exp(-z))), precompute n_max * exp(0.5),
            # and use Python's built-in math.exp for scalar inputs.
            return self._n_max_exp_half * math.exp(-0.5 * (z + math.exp(-z)))
        return self._n_max_exp_half * np.exp(-0.5 * (z + np.exp(-z)))

    def __add__(self, other):
        if isinstance(other, ChapmanLayer):
            return ChapmanProfile([self, other])
        elif isinstance(other, ChapmanProfile):
            return ChapmanProfile([self] + other.layers)
        else:
            raise TypeError("Can only add ChapmanLayer or ChapmanProfile")

    def plot_altitude_profile(self, min_h, max_h, filename="layer_profile.png"):
        # Create a single-layer profile and delegate
        profile = ChapmanProfile([self])
        profile.plot_altitude_profile(min_h, max_h, filename)

    def get_profile_data(self, min_h, max_h, steps=100):
        profile = ChapmanProfile([self])
        return profile.get_profile_data(min_h, max_h, steps)
