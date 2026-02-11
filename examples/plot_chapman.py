from alfven.ionosphere import ChapmanLayer

# Create E-layer (peak at 110km) and F-layer (peak at 300km)
e_layer = ChapmanLayer(h0=110, H=10, n_max=1e11)
f_layer = ChapmanLayer(h0=300, H=50, n_max=1e12)

profile = e_layer + f_layer
profile.plot_altitude_profile(0, 600, filename='chapman_profile.png')
