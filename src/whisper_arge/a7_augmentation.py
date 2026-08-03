"""Deterministic, on-the-fly A7 audio augmentation; never writes source audio."""

from __future__ import annotations

import hashlib

import librosa
import numpy as np
from scipy.signal import butter, resample_poly, sosfiltfilt


IMPLEMENTATION_ID = "A7_AUGMENTATION_POLICY_V3_UNIVERSAL_PEAK_GUARD"
MODEL_SAMPLE_RATE = 16000


def policy(bucket: str, seed: int) -> dict:
    snrs, gains = (10, 15, 20), (0, -3, -6)
    common = {"seed": seed, "output_sample_rate": MODEL_SAMPLE_RATE}
    if bucket == "phone_band":
        return {**common, "steps": ["bandpass_300_3400", "resample_8000", "resample_16000"]}
    if bucket == "speed_075":
        return {**common, "speed_factor": 0.75, "steps": ["time_stretch_0.75", "resample_16000"]}
    if bucket == "noise_gain":
        return {
            **common,
            "snr_db": snrs[seed % len(snrs)],
            "gain_db": gains[seed % len(gains)],
            "steps": ["band_limited_noise", "gain", "clipping_check"],
        }
    if bucket == "phone_band_noise_gain":
        return {
            **common,
            "snr_db": snrs[seed % len(snrs)],
            "gain_db": gains[seed % len(gains)],
            "steps": [
                "bandpass_300_3400",
                "resample_8000",
                "resample_16000",
                "band_limited_noise",
                "gain",
                "clipping_check",
            ],
        }
    return {**common, "steps": ["identity"]}


def _phone_band(audio: np.ndarray) -> np.ndarray:
    sos = butter(8, (300, 3400), btype="bandpass", fs=MODEL_SAMPLE_RATE, output="sos")
    filtered = sosfiltfilt(sos, audio).astype(np.float32)
    return resample_poly(resample_poly(filtered, 1, 2), 2, 1).astype(np.float32)


def _noise(audio: np.ndarray, seed: int, snr_db: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(audio.shape, dtype=np.float32)
    noise = _phone_band(noise)
    signal_rms, noise_rms = np.sqrt(np.mean(audio**2)), np.sqrt(np.mean(noise**2))
    if not np.isfinite(signal_rms) or signal_rms <= 0 or noise_rms <= 0:
        raise ValueError("invalid signal/noise RMS")
    scaled = noise * (signal_rms / (noise_rms * (10 ** (snr_db / 20))))
    return audio + scaled, scaled


def apply(audio: np.ndarray, bucket: str, seed: int) -> tuple[np.ndarray, dict]:
    """Apply the registered policy and fail rather than silently clip/normalize."""
    parameters = policy(bucket, seed)
    result = np.asarray(audio, dtype=np.float32).copy()
    if bucket in {"phone_band", "phone_band_noise_gain"}:
        result = _phone_band(result)
    if bucket == "speed_075":
        result = librosa.effects.time_stretch(result, rate=0.75).astype(np.float32)
    if bucket in {"noise_gain", "phone_band_noise_gain"}:
        result, noise = _noise(result, seed, int(parameters["snr_db"]))
        requested_gain = int(parameters["gain_db"])
        result = result * float(10 ** (requested_gain / 20))
        noise = noise * float(10 ** (requested_gain / 20))
        observed_peak = float(np.max(np.abs(result)))
        attenuation = min(0.0, float(20 * np.log10(0.98 / observed_peak))) if observed_peak else 0.0
        result = result * float(10 ** (attenuation / 20))
        noise = noise * float(10 ** (attenuation / 20))
        signal = result - noise
        measured_snr = float(
            20 * np.log10(np.sqrt(np.mean(signal**2)) / np.sqrt(np.mean(noise**2)))
        )
        parameters.update(
            {
                "requested_gain_db": requested_gain,
                "observed_peak_before_safety": observed_peak,
                "safety_attenuation_db": attenuation,
                "effective_total_gain_db": requested_gain + attenuation,
                "final_peak": float(np.max(np.abs(result))),
                "clipping_prevented": observed_peak > 0.98,
                "measured_snr_before_safety": measured_snr,
                "measured_snr_after_safety": measured_snr,
            }
        )
    observed_peak = float(np.max(np.abs(result)))
    universal_attenuation = (
        min(0.0, float(20 * np.log10(0.98 / observed_peak))) if observed_peak else 0.0
    )
    if bucket in {"phone_band", "speed_075"}:
        result = result * float(10 ** (universal_attenuation / 20))
        parameters.update(
            {
                "observed_peak_before_safety": observed_peak,
                "safety_attenuation_db": universal_attenuation,
                "final_peak": float(np.max(np.abs(result))),
                "clipping_prevented": observed_peak > 0.98,
            }
        )
    if not np.isfinite(result).all() or not result.size or not np.any(np.abs(result) > 1e-8):
        raise ValueError("invalid augmented tensor")
    if bucket in {"phone_band", "speed_075", "noise_gain", "phone_band_noise_gain"} and np.max(np.abs(result)) > 0.980001:
        raise ValueError("clipping-safe attenuation validation failed")
    parameters["effective_duration_seconds"] = len(result) / MODEL_SAMPLE_RATE
    parameters["tensor_sha256"] = hashlib.sha256(result.tobytes()).hexdigest()
    return result, parameters
