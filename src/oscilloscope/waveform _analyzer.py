#!/usr/bin/env python3
"""波形分析器 - 专为电源测试设计"""
import numpy as np
from typing import Dict, Tuple
from enum import Enum


class WaveformParameter(Enum):
    """波形关键参数"""
    VPP = "peak_to_peak"  # 峰峰值
    VRMS = "rms"  # 有效值
    RIPPLE = "ripple"  # 纹波
    NOISE = "noise"  # 噪声


class WaveformAnalyzer:
    """波形分析器"""

    def analyze_power_supply_waveform(self, voltage_data: np.ndarray) -> Dict[WaveformParameter, float]:
        """分析电源波形"""
        return {
            WaveformParameter.VPP: np.ptp(voltage_data),
            WaveformParameter.VRMS: np.sqrt(np.mean(voltage_data ** 2)),
            WaveformParameter.RIPPLE: self._calculate_ripple(voltage_data),
            WaveformParameter.NOISE: np.std(voltage_data)
        }

    def _calculate_ripple(self, data: np.ndarray) -> float:
        """计算纹波（AC分量）"""
        if len(data) < 100:
            return 0.0
        ac_component = data - np.mean(data)
        return np.std(ac_component)