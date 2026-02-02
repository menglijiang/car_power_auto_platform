#!/usr/bin/env python3
"""集成示波器监控的电源测试用例"""
import pytest
import time
from src.oscilloscope.keysight_controller import KeysightOscilloscopeController
from src.oscilloscope.waveform_analyzer import WaveformAnalyzer, WaveformParameter
from src.oscilloscope.pass_fail_evaluator import PassFailEvaluator


class TestPowerSupplyWithOscilloscope:
    """带示波器监控的电源测试"""

    @pytest.fixture
    def oscilloscope(self):
        """示波器夹具"""
        scope = KeysightOscilloscopeController("192.168.1.100")
        if scope.connect():
            # 应用电源测试预设
            scope.set_timebase(0.0001)  # 100us/div
            scope.set_channel_parameters(1, 0.01)  # 10mV/div
            yield scope
            scope.disconnect()
        else:
            pytest.skip("示波器连接失败")

    def test_48v_supply_ripple(self, power_supply, oscilloscope):
        """48V电源纹波测试 - 使用示波器监控"""
        # 设置电源参数
        power_supply.set_voltage(48.0)
        power_supply.set_current(5.0)
        power_supply.output_on()

        # 等待稳定
        time.sleep(2)

        # 捕获波形
        timestamps, voltage_data = oscilloscope.capture_waveform(1)

        # 分析波形
        analyzer = WaveformAnalyzer()
        parameters = analyzer.analyze_power_supply_waveform(voltage_data)

        # 判定结果
        evaluator = PassFailEvaluator()
        passed, detailed_results = evaluator.evaluate_test_result(parameters)

        # 生成测试报告
        self._generate_test_report(parameters, detailed_results, passed)

        # 断言
        assert passed, f"电源纹波测试失败: {detailed_results}"

    def _generate_test_report(self, parameters, detailed_results, passed):
        """生成测试报告"""
        report = {
            'test_name': '48V电源纹波测试',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'overall_result': 'PASS' if passed else 'FAIL',
            'parameters': {param.name: value for param, value in parameters.items()},
            'detailed_results': {
                param.name: {
                    'value': result['value'],
                    'threshold': result['threshold'],
                    'passed': result['passed']
                } for param, result in detailed_results.items()
            }
        }

        # 保存报告（可集成到现有报告系统）
        print(f"测试报告: {report}")