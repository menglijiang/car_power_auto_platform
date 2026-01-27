"""
汽车电源测试用例 - 使用pytest框架
"""
import sys
import os
import pytest
import time
import logging
from typing import Dict, Any

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.system_under_test.power_management import PowerManagement, TestResult, PowerState

# 配置测试日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_execution.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# 测试夹具
@pytest.fixture(scope="function")
def power_mgmt():
    """创建电源管理系统fixture（使用模拟器）"""
    pm = PowerManagement(use_simulator=True)
    yield pm
    # 测试后清理
    pm.emergency_shutdown()


@pytest.fixture(scope="session")
def test_config():
    """测试配置fixture"""
    return {
        "normal_voltage": 12.0,
        "high_voltage": 15.0,
        "low_voltage": 9.0,
        "max_current": 10.0,
        "voltage_tolerance": 0.1,  # 10%
        "sweep_test_range": {"start": 10.0, "end": 14.0, "step": 1.0}
    }


# 测试类
class TestPowerManagementBasic:
    """电源管理基础功能测试"""

    def test_initialization(self, power_mgmt):
        """测试系统初始化"""
        assert power_mgmt is not None
        assert power_mgmt.current_state == PowerState.OFF
        assert power_mgmt.safety_monitor_enabled is True
        assert len(power_mgmt.test_results) == 0

        # 验证日志记录
        logger.info("电源管理系统初始化测试通过")

    def test_emergency_shutdown(self, power_mgmt):
        """测试紧急关闭功能"""
        # 先设置状态为ON
        power_mgmt.current_state = PowerState.ON

        # 执行紧急关闭
        power_mgmt.emergency_shutdown()

        # 验证状态已改变
        assert power_mgmt.current_state == PowerState.OFF

        logger.info("紧急关闭功能测试通过")

    def test_voltage_validation_normal(self, power_mgmt):
        """测试正常电压验证"""
        # 测试在容差范围内的电压
        measured = 12.1
        expected = 12.0
        tolerance = 0.1  # 10%

        is_valid, message = power_mgmt._validate_voltage(measured, expected)

        assert is_valid is True
        assert "在范围" in message
        logger.info(f"电压验证测试通过: {message}")

    def test_voltage_validation_out_of_range(self, power_mgmt):
        """测试超出范围的电压验证"""
        # 测试超出容差范围的电压
        measured = 13.5  # 超出12V±10%
        expected = 12.0

        is_valid, message = power_mgmt._validate_voltage(measured, expected)

        assert is_valid is False
        assert "超出范围" in message
        logger.info(f"电压验证测试通过: {message}")

    def test_current_validation_normal(self, power_mgmt):
        """测试正常电流验证"""
        measured = 5.0
        max_current = 10.0

        is_valid, message = power_mgmt._validate_current(measured)

        assert is_valid is True
        assert "未超过限制" in message
        logger.info(f"电流验证测试通过: {message}")

    def test_current_validation_exceed(self, power_mgmt):
        """测试超出限制的电流验证"""
        measured = 12.0  # 超出10A限制
        max_current = 10.0

        is_valid, message = power_mgmt._validate_current(measured)

        assert is_valid is False
        assert "超过限制" in message
        logger.info(f"电流验证测试通过: {message}")


class TestPowerOnSequence:
    """上电序列测试"""

    @pytest.mark.smoke
    def test_normal_power_on_sequence(self, power_mgmt):
        """测试正常上电序列（冒烟测试）"""
        logger.info("开始正常上电序列测试")

        success, details = power_mgmt.perform_power_on_sequence(voltage=12.0)

        # 验证结果
        assert success is True
        assert details["final_result"] == "PASS"
        assert len(details["steps"]) >= 3
        assert len(details["measurements"]) > 0
        assert power_mgmt.current_state == PowerState.ON

        logger.info(f"正常上电序列测试通过，测量次数: {len(details['measurements'])}")

    @pytest.mark.parametrize("voltage, expected_pass", [
        (11.0, True),  # 在容差范围内
        (12.0, True),  # 正好目标值
        (13.0, True),  # 在容差范围内
        (9.0, False),  # 低于正常范围
        (15.0, False),  # 高于正常范围
    ])
    def test_power_on_with_different_voltages(self, power_mgmt, voltage, expected_pass):
        """参数化测试：不同电压下的上电序列"""
        logger.info(f"测试上电序列，电压: {voltage}V")

        success, details = power_mgmt.perform_power_on_sequence(voltage=voltage)

        if expected_pass:
            assert success is True, f"电压{voltage}V应通过但失败了"
            assert details["final_result"] == "PASS"
        else:
            assert success is False, f"电压{voltage}V应失败但通过了"
            assert details["final_result"] == "FAIL"
            assert len(details["errors"]) > 0

        logger.info(f"电压{voltage}V测试完成，结果: {'通过' if success else '失败'}")

    def test_power_on_sequence_with_error_handling(self, power_mgmt, monkeypatch):
        """测试上电序列的错误处理"""
        logger.info("测试上电序列错误处理")

        # 模拟测量时抛出异常
        def mock_measure_voltage():
            raise Exception("模拟硬件通信错误")

        monkeypatch.setattr(power_mgmt.ps_driver, 'measure_voltage', mock_measure_voltage)

        success, details = power_mgmt.perform_power_on_sequence(voltage=12.0)

        # 验证异常被捕获并处理
        assert success is False
        assert details["final_result"] == "FAIL"
        assert len(details["errors"]) > 0
        assert "模拟硬件通信错误" in str(details["errors"])

        logger.info("上电序列错误处理测试通过")


class TestVoltageSweep:
    """电压扫描测试"""

    @pytest.mark.slow
    def test_voltage_sweep_normal_range(self, power_mgmt, test_config):
        """测试正常电压范围扫描"""
        logger.info("开始电压扫描测试")

        sweep_range = test_config["sweep_test_range"]
        results = power_mgmt.perform_voltage_sweep_test(
            start_v=sweep_range["start"],
            end_v=sweep_range["end"],
            step_v=sweep_range["step"],
            dwell_time=0.1
        )

        # 验证结果
        assert len(results) == 5  # 10, 11, 12, 13, 14
        assert all(isinstance(r, TestResult) for r in results)

        # 验证每个测试点都有数据
        for result in results:
            assert result.test_name.startswith("电压扫描_")
            assert result.units == "V"
            assert "current" in result.details
            assert "target_voltage" in result.details

        logger.info(f"电压扫描测试完成，测试点数量: {len(results)}")

    def test_voltage_sweep_reverse_range(self, power_mgmt):
        """测试反向电压扫描（从高到低）"""
        logger.info("开始反向电压扫描测试")

        results = power_mgmt.perform_voltage_sweep_test(
            start_v=14.0,
            end_v=10.0,
            step_v=1.0,
            dwell_time=0.1
        )

        # 验证有5个测试点
        assert len(results) == 5

        # 检查电压值
        voltages = [result.details["target_voltage"] for result in results]
        assert voltages == [14.0, 13.0, 12.0, 11.0, 10.0]

        logger.info(f"反向电压扫描测试完成，电压序列: {voltages}")


class TestTestResultsManagement:
    """测试结果管理测试"""

    def test_test_summary(self, power_mgmt):
        """测试获取测试摘要功能"""
        # 先执行一些测试
        power_mgmt.perform_power_on_sequence(voltage=12.0)
        power_mgmt.perform_voltage_sweep_test(10.0, 12.0, 1.0)

        summary = power_mgmt.get_test_summary()

        # 验证摘要数据
        assert summary["total_tests"] > 0
        assert "passed_tests" in summary
        assert "failed_tests" in summary
        assert "pass_rate" in summary
        assert "current_state" in summary
        assert "timestamp" in summary

        logger.info(f"测试摘要: 总数={summary['total_tests']}, 通过率={summary['pass_rate']:.1f}%")

    def test_save_results_to_csv(self, power_mgmt, tmp_path):
        """测试保存结果到CSV文件"""
        # 先执行一些测试
        power_mgmt.perform_power_on_sequence(voltage=12.0)

        # 保存到临时文件
        csv_file = tmp_path / "test_results.csv"
        success = power_mgmt.save_results_to_csv(str(csv_file))

        assert success is True
        assert csv_file.exists()

        # 验证文件内容
        import csv
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0

        logger.info(f"测试结果已保存到: {csv_file}")


# 标记测试
@pytest.mark.smoke
def test_smoke_test_suite(power_mgmt):
    """冒烟测试套件"""
    logger.info("执行冒烟测试套件")

    # 测试1: 上电序列
    success, _ = power_mgmt.perform_power_on_sequence(voltage=12.0)
    assert success is True

    # 测试2: 电压扫描
    results = power_mgmt.perform_voltage_sweep_test(11.0, 13.0, 1.0)
    assert len(results) == 3

    # 测试3: 测试摘要
    summary = power_mgmt.get_test_summary()
    assert summary["total_tests"] == 4  # 1个上电 + 3个扫描

    logger.info("冒烟测试套件通过")


# 跳过需要真实硬件的测试
@pytest.mark.skip(reason="需要真实硬件连接")
def test_hardware_integration():
    """需要真实硬件的集成测试"""
    # 这个测试需要真实的硬件连接
    # 在没有硬件时会跳过
    pass


# 测试执行配置
def pytest_generate_tests(metafunc):
    """pytest测试生成钩子"""
    # 这里可以添加参数化测试的生成逻辑
    pass


# 命令行执行
if __name__ == "__main__":
    # 直接运行此文件时，使用pytest.main执行测试
    import pytest

    # 设置测试参数
    test_args = [
        "-v",  # 详细输出
        "--tb=short",  # 简短的错误回溯
        "--capture=no",  # 显示print输出
        "--log-level=INFO",  # 日志级别
        __file__  # 当前文件
    ]

    # 运行测试
    exit_code = pytest.main(test_args)
    sys.exit(exit_code)
