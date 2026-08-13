from .base import Backend


class WindowsBackend(Backend):
    """Reads temps/fans from LibreHardwareMonitor or OpenHardwareMonitor if one
    of them is running (they publish a WMI namespace), and falls back to the
    ACPI thermal zone which most machines expose at least partially."""

    name = "windows"

    def __init__(self):
        self._hwmon = None
        self._acpi = None
        self._connected = False

    def _connect(self):
        if self._connected:
            return
        self._connected = True
        try:
            import pythoncom
            import wmi
            pythoncom.CoInitialize()
        except Exception:
            return
        for namespace in (r"root\LibreHardwareMonitor", r"root\OpenHardwareMonitor"):
            try:
                conn = wmi.WMI(namespace=namespace)
                conn.Sensor()
                self._hwmon = conn
                return
            except Exception:
                continue
        try:
            self._acpi = wmi.WMI(namespace=r"root\wmi")
        except Exception:
            pass

    def temps(self):
        self._connect()
        out = {}
        if self._hwmon:
            try:
                for s in self._hwmon.Sensor(SensorType="Temperature"):
                    if s.Value:
                        out[s.Name] = float(s.Value)
            except Exception:
                pass
        if not out and self._acpi:
            try:
                for i, zone in enumerate(self._acpi.MSAcpi_ThermalZoneTemperature()):
                    celsius = zone.CurrentTemperature / 10.0 - 273.15
                    if -20 < celsius < 130:
                        out[f"Thermal zone {i}"] = celsius
            except Exception:
                pass
        return out

    def fans(self):
        self._connect()
        out = {}
        if self._hwmon:
            try:
                for s in self._hwmon.Sensor(SensorType="Fan"):
                    if s.Value:
                        out[s.Name] = int(s.Value)
            except Exception:
                pass
        return out
