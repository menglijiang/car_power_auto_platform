#!/usr/bin/env python3
"""安全监控测试用例"""
import pytest
from src.system_under_test.safety_monitor import SafetyMonitor, FaultType, SafetyState


class TestSafetyMonitoring:
    def test_over_voltage_protection(self):
        """测试HP侧过压保护（文档2.3.3.1）"""
        monitor = SafetyMonitor()

        # 模拟过压条件（71V > 70V阈值）
        monitor.update_measurements({
            'hp_voltage': 71.0,  # 超过70V阈值
            'lp_voltage': 14.0,
            'output_current': 10.0,
            'temperatures': [25.0, 25.0]
        })

        assert monitor.current_state == SafetyState.FAULT
        assert len(monitor.fault_history) > 0