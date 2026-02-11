from .utils import m_p, mu_0, Re

class Magnetopause:
    def __init__(self, density, velocity, Bz=0):
        """
        Initialize Magnetopause model.

        Args:
            density (float): Solar wind density in m^-3.
            velocity (float): Solar wind velocity in m/s.
            Bz (float): IMF Bz component in Tesla. Default 0.
        """
        self.density = density
        self.velocity = velocity
        self.Bz = Bz
        self.B0 = 3.12e-5 # Earth's magnetic field at equator in Tesla (31,200 nT)

    @property
    def radius_re(self):
        """
        Calculate the standoff distance in Earth Radii (Re).
        Using Chapman-Ferraro pressure balance (simplified):
        (R/Re)^6 = B0^2 / (mu_0 * rho * v^2)
        Assuming specular reflection (factor of 2 in dynamic pressure).
        """
        rho = self.density * m_p
        P_dyn = rho * self.velocity**2

        # Pressure balance:
        # Dynamic Pressure P_sw = 2 * rho * v^2 (specular reflection) ?
        # Or just rho * v^2 ?
        # Standard Chapman-Ferraro distance formula often cited is:
        # R_mp / Re = (B0^2 / (mu_0 * rho * v^2))^(1/6)
        # This corresponds to P_sw = rho * v^2 balancing B^2/2mu0 where B = 2*B_dipole.
        # Let's stick to this common form.

        if P_dyn <= 0:
            return float('inf')

        R_ratio_6 = self.B0**2 / (mu_0 * P_dyn)
        return R_ratio_6**(1/6)
