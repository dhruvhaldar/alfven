from alfven.magnetosphere import Magnetopause

# Solar Wind Conditions (Normal vs Storm)
normal = Magnetopause(density=5e6, velocity=400e3) # 5 cm^-3, 400 km/s
storm  = Magnetopause(density=20e6, velocity=800e3) # CME Impact

print(f"Normal Standoff: {normal.radius_re:.1f} Re")
print(f"Storm Standoff:  {storm.radius_re:.1f} Re")
