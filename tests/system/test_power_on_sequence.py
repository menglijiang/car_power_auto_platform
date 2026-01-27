# tests/system/test_power_on_sequence.py
import pytest
import allure


@allure.feature("电源上电序列测试")
class TestPowerOnSequence:

    @allure.story("正常电压上电")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_normal_power_on(self, power_system):
        """测试在正常电压下，上电序列是否成功，DUT状态是否正确[1](@ref)"""
        with allure.step("执行标准上电序列"):
            test_result, measured_voltage = power_system.perform_power_on_sequence()

        with allure.step("验证测试结果"):
            assert test_result is True, f"上电序列失败。测量电压: {measured_voltage}V 未在正常范围内"
            allure.attach(f"实测电压: {measured_voltage}V", "电压读数", allure.attachment_type.TEXT)