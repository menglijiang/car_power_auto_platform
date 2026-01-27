# src/drivers/pmbus_driver.py
import smbus2


class PMBusDriver:
    """PMBUS通信驱动 - 文档2.3.3要求"""

    def __init__(self, bus_num=1, address=0x40):
        self.bus = smbus2.SMBus(bus_num)
        self.address = address

    def read_temperature(self) -> list:
        """读取温度数据 - 2个NTC传感器"""
        # 文档2.3.3要求输入输出侧各1个NTC
        return [self._read_ntc(0), self._read_ntc(1)]

    def read_current(self) -> float:
        """读取电流值 - 支持过流保护监控"""
        return self._read_pmbus_register(0x8C)  # READ_IOUT

    def set_protection_thresholds(self, thresholds: dict):
        """设置保护阈值 - 文档2.3.3可配置要求"""
        self._write_pmbus_register(0x55, thresholds['ocp_fast'])  # 快速过流
        self._write_pmbus_register(0x56, thresholds['ocp_slow'])  # 慢速过流