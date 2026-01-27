# power_supply_driver.py
import pyvisa


class PowerSupplyDriver:
    """封装可编程电源的操作，提供高级API"""

    def __init__(self, resource_addr):
        self.rm = pyvisa.ResourceManager()
        try:
            self.instrument = self.rm.open_resource(resource_addr)
            self.instrument.timeout = 5000
        except pyvisa.Error as e:
            raise Exception(f"无法连接到电源设备 {resource_addr}: {e}")

    def set_voltage(self, voltage):
        """设置输出电压"""
        self.instrument.write(f"SOUR:VOLT {voltage}")

    def measure_output_current(self):
        """测量实际输出电流"""
        return float(self.instrument.query("MEAS:CURR?"))

    def enable_output(self, enable=True):
        """开启或关闭输出（安全关键操作）"""
        state = "ON" if enable else "OFF"
        self.instrument.write(f"OUTP {state}")