import subprocess

from .linux import LinuxBackend

FLAG_BITS = {
    0: "undervoltage_now",
    1: "freq_capped_now",
    2: "throttled_now",
    3: "soft_temp_limit_now",
    16: "undervoltage_past",
    17: "freq_capped_past",
    18: "throttled_past",
    19: "soft_temp_limit_past",
}


def _vcgencmd(*args) -> str | None:
    try:
        return subprocess.check_output(
            ["vcgencmd", *args], text=True, timeout=2, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return None


class PiBackend(LinuxBackend):
    name = "raspberry-pi"

    def temps(self):
        out = super().temps()
        if not out:
            raw = _vcgencmd("measure_temp")
            if raw and "=" in raw:
                try:
                    out["SoC"] = float(raw.split("=")[1].rstrip("'C"))
                except ValueError:
                    pass
        return out

    def pi_flags(self) -> dict[str, bool]:
        raw = _vcgencmd("get_throttled")
        if not raw or "=" not in raw:
            return {}
        try:
            bits = int(raw.split("=")[1], 16)
        except ValueError:
            return {}
        return {label: bool(bits >> bit & 1) for bit, label in FLAG_BITS.items()}

    def extras(self):
        return {"pi": self.pi_flags()}

    def throttle_state(self, freq_cur, freq_max, hottest, load):
        flags = self.pi_flags()
        if flags.get("throttled_now") or flags.get("soft_temp_limit_now"):
            return {"active": True, "reason": "thermal"}
        if flags.get("undervoltage_now"):
            return {"active": True, "reason": "undervoltage"}
        if flags.get("freq_capped_now"):
            return {"active": True, "reason": "power"}
        return super().throttle_state(freq_cur, freq_max, hottest, load)
