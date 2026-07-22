import pytest

from weather_api.services.weather import _normalize_current


def _observation(temperature_c=None, dewpoint_c=None):
    """Build a minimal NWS observation payload."""
    def _val(v):
        return {"value": v, "unitCode": "wmoUnit:degC"}

    props = {}
    if temperature_c is not None:
        props["temperature"] = _val(temperature_c)
    if dewpoint_c is not None:
        props["dewpoint"] = _val(dewpoint_c)
    return {"properties": props}


def test_feels_like_both_present():
    result = _normalize_current(_observation(temperature_c=20.0, dewpoint_c=15.0))
    # avg of 20 and 15 = 17.5 C → 63.5 F
    assert result.feels_like_f == pytest.approx(63.5, abs=0.1)


def test_feels_like_no_dewpoint():
    result = _normalize_current(_observation(temperature_c=25.0))
    # fallback to temperature: 25 C → 77.0 F
    assert result.feels_like_f == pytest.approx(77.0, abs=0.1)


def test_feels_like_no_temperature():
    # Regression: NWS returns dewpoint but not temperature — must not raise TypeError
    result = _normalize_current(_observation(dewpoint_c=10.0))
    assert result.feels_like_f is None


def test_feels_like_both_missing():
    result = _normalize_current(_observation())
    assert result.temperature_f is None
    assert result.feels_like_f is None
