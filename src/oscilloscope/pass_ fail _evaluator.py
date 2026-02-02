#!/usr/bin/env python3
"""通过/失败判定器"""
from typing import Dict, Tuple
from .waveform_analyzer import WaveformParameter


class PassFailEvaluator:
    """测试结果判定器"""

    def __init__(self):
        # 48V电源测试阈值配置
        self.thresholds = {
            WaveformParameter.VPP: 0.1,  # 100mV峰峰值
            WaveformParameter.RIPPLE: 0.05,  # 50mV纹波
            WaveformParameter.NOISE: 0.02  # 20mV噪声
        }

    def evaluate_test_result(self, parameters: Dict[WaveformParameter, float]) -> Tuple[bool, Dict]:
        """判定测试结果"""
        results = {}
        all_passed = True

        for param, value in parameters.items():
            if param in self.thresholds:
                threshold = self.thresholds[param]
                passed = value <= threshold
                results[param] = {
                    'value': value,
                    'threshold': threshold,
                    'passed': passed
                }
                if not passed:
                    all_passed = False

        return all_passed, results