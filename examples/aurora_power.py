from alfven.aurora import AuroraPower

# Estimate power for a moderate substorm
# E = 50 mV/m
# Sigma_P = 10 S
# Area = 2000 km x 500 km (Auroral Arc) = 1e12 m^2

ap = AuroraPower(E_field=0.05, sigma_P=10, area=1e12)

print(f"Sheet Current Density: {ap.sheet_current} A/m")
print(f"Total Dissipated Power: {ap.dissipated_power / 1e9:.2f} GW")
