"""Tests for the probe geometry engine and the shipped configurations."""

from pathlib import Path

import pytest

from probe_design import ProbeLayout, distance, is_blocked, midpoint

CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"
CONFIGS = sorted(CONFIG_DIR.glob("*.json"))

# Separations targeted across every probe in the setup, in centimetres.
TARGET_SDS = {"fdcs": 1.80, "fnirs": 2.90}

# Layouts are rounded to a printable grid, so realised separations sit within
# a millimetre of the target rather than exactly on it.
LAYOUT_TOLERANCE_CM = 0.1


# ----------------------------------------------------------------------
# Geometry primitives
# ----------------------------------------------------------------------
def test_distance_is_euclidean():
    assert distance([0, 0], [3, 4]) == pytest.approx(5.0)


def test_midpoint():
    assert midpoint([0, 0], [4, 2]) == (2.0, 1.0)


def test_obstacle_on_the_segment_is_flagged():
    assert is_blocked([0, 0], [4, 0], obstacles=[[2, 0.1]], buffer=0.3)


def test_obstacle_far_from_the_segment_is_not_flagged():
    assert not is_blocked([0, 0], [4, 0], obstacles=[[2, 1.0]], buffer=0.3)


def test_obstacle_beyond_the_endpoints_is_not_flagged():
    # Projection falls outside the segment, so it is not between the pair.
    assert not is_blocked([0, 0], [4, 0], obstacles=[[6, 0.0]], buffer=0.3)


def test_endpoints_are_not_treated_as_obstacles():
    assert not is_blocked([0, 0], [4, 0], obstacles=[[0, 0], [4, 0]], buffer=0.3)


# ----------------------------------------------------------------------
# Shipped configurations
# ----------------------------------------------------------------------
@pytest.mark.parametrize("config", CONFIGS, ids=lambda p: p.stem)
def test_config_loads(config):
    layout = ProbeLayout.from_json(config)
    assert layout.width > 0 and layout.height > 0
    assert layout.name


@pytest.mark.parametrize("config", CONFIGS, ids=lambda p: p.stem)
def test_every_component_sits_inside_the_probe_outline(config):
    layout = ProbeLayout.from_json(config)
    for label, (x, y) in layout.labels.items():
        assert 0 <= x <= layout.width, f"{label} outside probe in {config.stem}"
        assert 0 <= y <= layout.height, f"{label} outside probe in {config.stem}"


@pytest.mark.parametrize("config", CONFIGS, ids=lambda p: p.stem)
def test_every_layout_yields_at_least_one_admissible_pair_per_modality(config):
    layout = ProbeLayout.from_json(config)
    assert layout.channels("fnirs"), f"no fNIRS pair in {config.stem}"
    assert layout.channels("fdcs"), f"no fDCS pair in {config.stem}"


@pytest.mark.parametrize("config", CONFIGS, ids=lambda p: p.stem)
def test_admissible_pairs_respect_their_sds_window(config):
    layout = ProbeLayout.from_json(config)
    for channel in layout.all_channels():
        low, high = layout.sds_limits[channel.modality]
        assert low <= channel.sds <= high


def test_final_lateral_probe_hits_the_target_separations():
    """The lateral probe is the reference: 1.80 cm fDCS, 2.90 cm fNIRS."""
    layout = ProbeLayout.from_json(CONFIG_DIR / "lateral_final.json")
    assert {round(c.sds, 2) for c in layout.channels("fdcs")} == {TARGET_SDS["fdcs"]}
    assert {round(c.sds, 2) for c in layout.channels("fnirs")} == {TARGET_SDS["fnirs"]}


def test_lateral_and_occipital_probes_use_matched_separations():
    """Matched separations keep acquisition geometry from confounding the comparison.

    The occipital probe is built to the same nominal separations as the
    lateral one; residual sub-millimetre offsets come from rounding the optode
    centres to the printable grid.
    """
    lateral = ProbeLayout.from_json(CONFIG_DIR / "lateral_final.json")
    occipital = ProbeLayout.from_json(CONFIG_DIR / "occipital.json")

    for modality, target in TARGET_SDS.items():
        for probe in (lateral, occipital):
            for channel in probe.channels(modality):
                assert channel.sds == pytest.approx(
                    target, abs=LAYOUT_TOLERANCE_CM
                ), f"{probe.name}: {channel} deviates from the {target} cm target"


def test_final_lateral_probe_has_four_fdcs_pairs():
    layout = ProbeLayout.from_json(CONFIG_DIR / "lateral_final.json")
    assert len(layout.channels("fdcs")) == 4


def test_report_uses_singular_and_plural_correctly():
    layout = ProbeLayout.from_json(CONFIG_DIR / "lateral_final.json")
    report = layout.report()
    assert "1 source, 4 detectors" in report
    assert "1 sources" not in report
