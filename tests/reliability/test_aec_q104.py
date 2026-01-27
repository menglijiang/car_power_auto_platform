# tests/reliability/test_aec_q104.py
import time
import pytest


class TestAECQ104Compliance:
    """AEC-Q104合规性测试 - 文档3.1节要求"""

    @pytest.mark.long_running
    def test_temperature_cycling(self):
        """温度循环测试 - 文档3.1.1要求"""
        # -40℃ to 105℃, 1000 cycles
        cycles = 1000
        for i in range(cycles):
            self._run_temperature_cycle(-40, 105)
            if i % 100 == 0:
                self._perform_functional_test()

    def test_drop_test(self):
        """模组跌落测试 - 文档3.1.4要求"""
        # 1500G加速度, 0.5ms, 30次冲击
        for impact in range(30):
            self._simulate_drop_impact(1500, 0.0005)
            self._verify_continuity()  # 菊花链连续性检查