#!/usr/bin/env python3
"""是德科技示波器具体实现"""
import numpy as np
from .base_controller import BaseOscilloscopeController, OscilloscopeSettings


class KeysightOscilloscopeController(BaseOscilloscopeController):
    """是德科技示波器控制器"""

    def __init__(self, ip_address: str):
        resource_string = f"TCPIP::{ip_address}::INSTR"
        super().__init__(resource_string)

    def set_timebase(self, scale: float, offset: float = 0.0):
        """设置时基参数"""
        self._send_command(f":TIMebase:SCALe {scale}")
        self._send_command(f":TIMebase:POSition {offset}")
        print(f"时基设置: {scale * 1000:.1f}ms/div")

    def set_channel_parameters(self, channel: int, scale: float, offset: float = 0.0):
        """设置通道参数"""
        self._send_command(f":CHANnel{channel}:DISPlay 1")
        self._send_command(f":CHANnel{channel}:SCALe {scale}")
        self._send_command(f":CHANnel{channel}:OFFSet {offset}")
        print(f"通道{channel}设置: {scale * 1000:.1f}mV/div")

    def capture_waveform(self, channel: int) -> Tuple[np.ndarray, np.ndarray]:
        """捕获波形数据"""
        self._send_command(f":WAVeform:SOURce CHANnel{channel}")
        self._send_command(":WAVeform:FORMat WORD")

        # 获取波形参数和数据
        x_increment = float(self._send_command(":WAVeform:XINCrement?"))
        x_origin = float(self._send_command(":WAVeform:XORigin?"))
        raw_data = self._send_command(":WAVeform:DATA?")

        # 转换数据格式
        y_values = np.frombuffer(bytes.fromhex(raw_data[10:]), dtype=np.uint16)
        x_values = np.arange(len(y_values)) * x_increment + x_origin

        return x_values, y_values

    def _send_command(self, command: str) -> str:
        """发送SCPI命令"""
        return self.instrument.query(command).strip()