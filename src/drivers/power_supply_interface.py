# src/drivers/power_supply_interface.py
class PowerSupplyInterface:
    """电源接口抽象层 - 符合文档2.1节接口定义"""

    def __init__(self):
        self.signals = {
            'HP': {'type': 'power', 'range': (-0.3, 70.0)},  # 高压侧
            'LP': {'type': 'power', 'range': (-0.3, 40.0)},  # 低压侧
            'EN': {'type': 'input', 'levels': [3.3, 5.0]},  # 使能信号
            'PG': {'type': 'output', 'od': True},  # Power Good
            'HB': {'type': 'output', 'optional': True},  # 心跳脉冲
            'PMBUS': {'type': 'communication'},  # 通信接口
            'ADDR': {'type': 'input', 'pullup': True}  # 地址识别
        }

    def read_hb_pulse(self) -> dict:
        """读取心跳脉冲 - 文档2.3.3要求10kHz 50%占空比"""
        return {
            'frequency': 10000,  # 10kHz
            'duty_cycle': 0.5,  # 50%
            'status': 'normal'  # 正常/异常
        }