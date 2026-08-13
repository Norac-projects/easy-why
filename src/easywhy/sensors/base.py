import psutil


class Backend:
    name = "generic"

    def temps(self) -> dict[str, float]:
        out = {}
        try:
            for chip, entries in psutil.sensors_temperatures().items():
                for entry in entries:
                    if not entry.current:
                        continue
                    key = f"{chip} {entry.label}".strip() if entry.label else chip
                    out[key] = entry.current
        except Exception:
            pass
        return out

    def fans(self) -> dict[str, int]:
        out = {}
        try:
            for chip, entries in psutil.sensors_fans().items():
                for entry in entries:
                    out[entry.label or chip] = entry.current
        except Exception:
            pass
        return out

    def throttle_state(self, freq_cur, freq_max, hottest, load) -> dict:
        # Only call it throttling when the machine is actually under load,
        # otherwise a low clock is just normal idle scaling.
        if freq_cur and freq_max and load >= 55 and freq_cur < freq_max * 0.85:
            reason = "thermal" if hottest and hottest >= 80 else "power"
            return {"active": True, "reason": reason}
        return {"active": False, "reason": ""}

    def extras(self) -> dict:
        return {}
