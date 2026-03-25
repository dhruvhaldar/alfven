from api.index import get_ionosphere_profile, IonosphereInput, LayerParams

import pytest

@pytest.mark.asyncio
async def test_ionosphere_profile_endpoint_logic():
    """
    Test that the ionosphere profile logic works correctly with the new optimization.
    """
    layers = [
        LayerParams(h0=300, H=50, n_max=1e12),
        LayerParams(h0=110, H=10, n_max=1e11)
    ]

    input_data = IonosphereInput(
        layers=layers,
        min_h=100,
        max_h=400,
        steps=5
    )

    result = await get_ionosphere_profile(input_data)

    assert "altitude" in result
    assert "density" in result
    assert len(result["altitude"]) == 5
    assert len(result["density"]) == 5

    # Check that density is non-zero (simple sanity check)
    assert any(d > 0 for d in result["density"])

@pytest.mark.asyncio
async def test_ionosphere_profile_empty_layers():
    """
    Test behavior with empty layers.
    """
    input_data = IonosphereInput(
        layers=[],
        min_h=100,
        max_h=400,
        steps=5
    )

    result = await get_ionosphere_profile(input_data)

    assert result["altitude"] == []
    assert result["density"] == []
