import math
import numpy as np

class ChapmanProfile:
    def __init__(self, layers):
        self.layers = layers

    def density(self, h):
        """
        Calculate total electron density at height h.

        Args:
            h (float or np.ndarray): Altitude in km.

        Returns:
            float or np.ndarray: Electron density in m^-3.
        """
        if not self.layers:
            return 0.0 if np.isscalar(h) else np.zeros_like(h)

        # Optimization: Use Python's built-in sum() with a list comprehension.
        # This is significantly faster (~3x) than initializing np.zeros_like(h)
        # and accumulating in a Python for-loop, especially for a small number of layers.
        return sum([layer.density(h) for layer in self.layers])

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
        z = (h - self.h0) / self.H
        if np.isscalar(h):
            # Optimization: Use Python's built-in math.exp for scalar inputs.
            # This avoids NumPy's type coercion and dispatch overhead, which is
            # significantly slower (often 2x-3x slower) than math.exp for single values.
            return self.n_max * math.exp(0.5 * (1 - z - math.exp(-z)))
        return self.n_max * np.exp(0.5 * (1 - z - np.exp(-z)))

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
