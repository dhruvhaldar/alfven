class AuroraPower:
    def __init__(self, E_field, sigma_P, area):
        """
        Estimate auroral power dissipation.

        Args:
            E_field (float): Electric field in V/m. Typical ~50 mV/m (0.05).
            sigma_P (float): Height-integrated Pedersen conductivity in Siemens (mho). Typical ~10 S.
            area (float): Auroral oval area in m^2.
        """
        self.E = E_field
        self.sigma_P = sigma_P
        self.area = area

    @property
    def dissipated_power(self):
        """
        Calculate total power dissipated (Joule heating) in Watts.
        P = Sigma_P * E^2 * Area
        """
        # Optimization: use direct multiplication instead of **2 for speed
        return self.sigma_P * (self.E * self.E) * self.area

    @property
    def sheet_current(self):
        """
        Calculate sheet current density (A/m).
        K = Sigma_P * E
        """
        return self.sigma_P * self.E
