"""Unit tests for the pure scoring/selection logic — no DB or external services."""
from __future__ import annotations

from app.pipeline.highlight import HighlightCell, fuse, resolve_weights
from app.pipeline.select import build_recut, pick_shorts
from app.pipeline.signals.base import SignalPoint


def _flat(name: str, score: float, duration: float = 100.0) -> list[SignalPoint]:
    return [SignalPoint(0.0, duration, score)]


def test_fuse_keep_signal_drives_score_up():
    signals = {"audio_energy": _flat("audio_energy", 1.0)}
    weights = {"audio_energy": 1.0}
    curve = fuse(signals, duration_s=10.0, weights=weights)
    assert curve, "expected non-empty curve"
    assert all(c.keep == 1.0 for c in curve)


def test_fuse_silence_is_inverted():
    # Silence has polarity -1: a high silence score should drive keep toward 0.
    signals = {"silence": _flat("silence", 1.0)}
    curve = fuse(signals, duration_s=10.0, weights={"silence": 1.0})
    assert all(c.keep == 0.0 for c in curve)


def test_fuse_weighted_mix():
    signals = {
        "audio_energy": _flat("audio_energy", 1.0),
        "silence": _flat("silence", 1.0),  # inverts to 0
    }
    # Equal weights → (1*1 + 1*(1-1)) / 2 = 0.5
    curve = fuse(signals, duration_s=5.0, weights={"audio_energy": 1.0, "silence": 1.0})
    assert all(abs(c.keep - 0.5) < 1e-9 for c in curve)


def test_fuse_empty_for_zero_duration():
    assert fuse({}, duration_s=0.0, weights={"audio_energy": 1.0}) == []


def test_presets_exist():
    for preset in ("balanced", "chaos", "storytime"):
        w = resolve_weights(preset)
        assert set(w) == {"silence", "audio_energy", "chat_velocity", "llm_humor"}


def _curve_with_peak(peak_start: int, peak_end: int, length: int = 200) -> list[HighlightCell]:
    cells = []
    for t in range(length):
        keep = 0.9 if peak_start <= t < peak_end else 0.1
        cells.append(HighlightCell(t_start=float(t), t_end=float(t + 1), keep=keep))
    return cells


def test_pick_shorts_finds_peak_and_clamps_length():
    curve = _curve_with_peak(50, 70)  # 20s peak, within [15,60]
    shorts = pick_shorts(curve)
    assert len(shorts) == 1
    s = shorts[0]
    assert 15.0 <= (s.t_end - s.t_start) <= 60.0
    assert s.t_start <= 50 and s.t_end >= 70


def test_pick_shorts_pads_short_peak_to_minimum():
    curve = _curve_with_peak(100, 105)  # only 5s above threshold
    shorts = pick_shorts(curve)
    assert len(shorts) == 1
    assert shorts[0].t_end - shorts[0].t_start >= 15.0 - 1e-6


def test_pick_shorts_non_overlapping_and_limited():
    # Two clearly separated peaks.
    curve = _curve_with_peak(20, 40)
    for c in curve[120:140]:
        object.__setattr__(c, "keep", 0.95)
    shorts = pick_shorts(curve, limit=5)
    # No two chosen intervals overlap.
    for a in shorts:
        for b in shorts:
            if a is not b:
                assert a.t_end <= b.t_start or a.t_start >= b.t_end


def test_build_recut_drops_dead_air():
    curve = _curve_with_peak(50, 70)  # only the peak is above recut threshold
    kept = build_recut(curve)
    assert len(kept) == 1
    assert kept[0].t_start <= 50 and kept[0].t_end >= 70
    # Dead air (low keep) excluded → kept span is far shorter than full timeline.
    assert (kept[0].t_end - kept[0].t_start) < 50
