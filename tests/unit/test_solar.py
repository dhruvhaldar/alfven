from alfven.solar import ParkerSpiral, sunspot_temperature

def test_parker_spiral():
    ps = ParkerSpiral(v_sw=400000)
    # At 1 AU, angle ~ 45 deg
    angle = ps.spiral_angle(1.5e11)
    assert abs(angle - 45) < 5

def test_sunspot():
    # Intensity ratio 0.5
    # T_spot / T_phot = (0.5)^0.25 = 0.840896
    # 5778 * 0.840896 ~ 4858 K
    temp = sunspot_temperature(0.5)
    assert abs(temp - 4858) < 10
