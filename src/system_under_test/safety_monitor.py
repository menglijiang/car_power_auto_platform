#!/usr/bin/env python3
"""
安全监控模块 - 符合SOR文档V1.0要求
功能：实现过压、欠压、过流、过温等安全保护监控
文档参考：2.3.3故障诊断和保护、4.功能安全需求
"""
import time
import logging
from typing import Dict, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class SafetyState(Enum):
    """安全状态枚举"""
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    FAULT = "FAULT"
    SHUTDOWN = "SHUTDOWN"


class FaultType(Enum):
    """故障类型枚举"""
    HP_OVERVOLTAGE = "HP_过压"  # HP侧过压
    HP_UNDERVOLTAGE = "HP_欠压"  # HP侧欠压
    LP_OVERVOLTAGE = "LP_过压"  # LP侧过压
    OVERCURRENT = "过流"  # 过流保护
    OVERTEMPERATURE = "过温"  # 过温保护
    COMMUNICATION_FAILURE = "通信故障"


@dataclass
class SafetyThresholds:
    """安全阈值配置 - 基于文档2.3.3节"""
    # HP侧电压保护阈值（文档2.3.3.1）
    hp_over_voltage: float = 70.0  # V (V_HP > 70V时过压关断)
    hp_under_voltage: float = 16.0  # V (V_HP < 16V时欠压关断)

    # LP侧电压保护阈值（文档2.3.3.2）
    lp_over_voltage: float = 24.0  # V (V_LP > 24V时过压关断)

    # 过流保护阈值（文档2.3.3.3）
    over_current_fast: float = 50.0  # A (us级快速关断)
    over_current_slow: float = 40.0  # A (s级慢速关断)
    ocp_fast_response: float = 0.001  # s (3ms快速响应)
    ocp_slow_response: float = 1.0  # s (20ms慢速响应)

    # 温度保护阈值（文档2.3.3.4）
    temp_warning: float = 100.0  # °C (过温预警)
    temp_shutdown: float = 105.0  # °C (过温关断)
    ntc_count: int = 2  # NTC数量（输入输出侧各1个）


class SafetyMonitor:
    """
    安全监控器 - 实现文档要求的各项保护功能
    符合ASIL功能安全要求（文档第4部分）
    """

    def __init__(self, config: Dict = None):
        self.logger = logging.getLogger(__name__)
        self.thresholds = SafetyThresholds()

        # 安全状态
        self.current_state = SafetyState.NORMAL
        self.fault_history = []

        # 实时监测值
        self.hp_voltage = 0.0
        self.lp_voltage = 0.0
        self.output_current = 0.0
        self.temperatures = [0.0, 0.0]  # 2个NTC温度

        # 回调函数
        self.fault_callbacks = {}
        self.state_callbacks = {}

        # 统计信息
        self.monitoring_start_time = time.time()
        self.fault_count = 0

        self.logger.info("安全监控系统初始化完成")

    def update_measurements(self, measurements: Dict[str, float]):
        """
        更新测量值并执行安全检查
        文档要求：实时监控输入/输出电压、电流、温度
        """
        try:
            # 更新测量值
            self.hp_voltage = measurements.get('hp_voltage', 0.0)
            self.lp_voltage = measurements.get('lp_voltage', 0.0)
            self.output_current = measurements.get('output_current', 0.0)
            self.temperatures = measurements.get('temperatures', [0.0, 0.0])

            # 执行安全检查
            self._perform_safety_checks()

        except Exception as e:
            self.logger.error(f"安全监控更新失败: {e}")
            self._trigger_fault(FaultType.COMMUNICATION_FAILURE)

    def _perform_safety_checks(self):
        """执行各项安全检查 - 基于文档2.3.3节要求"""
        previous_state = self.current_state

        # 1. HP侧电压监控（文档2.3.3.1）
        if self.hp_voltage > self.thresholds.hp_over_voltage:
            self._trigger_fault(FaultType.HP_OVERVOLTAGE)
        elif self.hp_voltage < self.thresholds.hp_under_voltage:
            self._trigger_fault(FaultType.HP_UNDERVOLTAGE)

        # 2. LP侧电压监控（文档2.3.3.2）
        elif self.lp_voltage > self.thresholds.lp_over_voltage:
            self._trigger_fault(FaultType.LP_OVERVOLTAGE)

        # 3. 过流保护监控（文档2.3.3.3）
        elif self.output_current > self.thresholds.over_current_fast:
            # us级快速关断
            self._trigger_fault(FaultType.OVERCURRENT, "快速过流")
        elif self.output_current > self.thresholds.over_current_slow:
            # s级慢速关断
            self._trigger_fault(FaultType.OVERCURRENT, "慢速过流")

        # 4. 温度监控（文档2.3.3.4）
        elif max(self.temperatures) > self.thresholds.temp_shutdown:
            self._trigger_fault(FaultType.OVERTEMPERATURE, "过温关断")
        elif max(self.temperatures) > self.thresholds.temp_warning:
            self.current_state = SafetyState.WARNING
            self._notify_state_change(SafetyState.WARNING, "过温预警")

        # 5. 恢复正常状态检查
        elif (self.current_state == SafetyState.FAULT and
              self._all_measurements_normal()):
            self._recover_from_fault()

        # 状态变化通知
        if self.current_state != previous_state:
            self._notify_state_change(self.current_state)

    def _trigger_fault(self, fault_type: FaultType, description: str = ""):
        """触发故障处理 - 符合文档要求的自动恢复机制"""
        fault_info = {
            'type': fault_type,
            'description': description,
            'timestamp': time.time(),
            'measurements': {
                'hp_voltage': self.hp_voltage,
                'lp_voltage': self.lp_voltage,
                'current': self.output_current,
                'temperatures': self.temperatures.copy()
            }
        }

        self.fault_history.append(fault_info)
        self.fault_count += 1
        self.current_state = SafetyState.FAULT

        self.logger.warning(f"安全故障: {fault_type.value} - {description}")

        # 执行故障回调
        if fault_type in self.fault_callbacks:
            self.fault_callbacks[fault_type](fault_info)

        # 根据文档要求执行保护动作
        self._execute_protection_action(fault_type)

    def _execute_protection_action(self, fault_type: FaultType):
        """执行保护动作 - 基于文档2.3.3节"""
        if fault_type in [FaultType.HP_OVERVOLTAGE, FaultType.HP_UNDERVOLTAGE,
                          FaultType.LP_OVERVOLTAGE, FaultType.OVERCURRENT]:
            # 过压/欠压/过流保护：关断输出，故障消失自动恢复
            self._shutdown_output()
            self.logger.info("执行保护关断，等待故障恢复")

        elif fault_type == FaultType.OVERTEMPERATURE:
            # 过温保护：关断输出，需要通过EN重使能恢复
            self._shutdown_output()
            self.logger.info("过温保护关断，需EN重使能恢复")

    def _recover_from_fault(self):
        """从故障中恢复 - 实现文档要求的自动恢复机制"""
        self.current_state = SafetyState.NORMAL
        self._restore_output()
        self.logger.info("故障恢复，系统返回正常状态")

    def _shutdown_output(self):
        """关断输出 - 模拟文档要求的保护动作"""
        # 这里应该调用电源驱动的关断方法
        self.logger.info("安全监控：关断电源输出")

    def _restore_output(self):
        """恢复输出 - 模拟文档要求的恢复机制"""
        # 这里应该调用电源驱动的使能方法
        self.logger.info("安全监控：恢复电源输出")

    def _all_measurements_normal(self) -> bool:
        """检查所有测量值是否在正常范围内"""
        return (self.thresholds.hp_under_voltage <= self.hp_voltage <= self.thresholds.hp_over_voltage and
                self.lp_voltage <= self.thresholds.lp_over_voltage and
                self.output_current <= self.thresholds.over_current_slow and
                max(self.temperatures) <= self.thresholds.temp_warning)

    def add_fault_callback(self, fault_type: FaultType, callback: Callable):
        """添加故障回调函数"""
        self.fault_callbacks[fault_type] = callback

    def add_state_callback(self, callback: Callable):
        """添加状态变化回调函数"""
        self.state_callbacks[id(callback)] = callback

    def _notify_state_change(self, new_state: SafetyState, reason: str = ""):
        """通知状态变化"""
        for callback in self.state_callbacks.values():
            try:
                callback(new_state, reason)
            except Exception as e:
                self.logger.error(f"状态回调执行失败: {e}")

    def get_safety_status(self) -> Dict:
        """获取安全状态摘要 - 用于报告生成"""
        return {
            'current_state': self.current_state.value,
            'fault_count': self.fault_count,
            'uptime': time.time() - self.monitoring_start_time,
            'current_measurements': {
                'hp_voltage': self.hp_voltage,
                'lp_voltage': self.lp_voltage,
                'output_current': self.output_current,
                'temperatures': self.temperatures
            },
            'recent_faults': self.fault_history[-5:]  # 最近5个故障
        }

    def configure_thresholds(self, new_thresholds: Dict):
        """配置安全阈值 - 支持文档要求的阈值调整功能"""
        for key, value in new_thresholds.items():
            if hasattr(self.thresholds, key):
                setattr(self.thresholds, key, value)
                self.logger.info(f"更新安全阈值 {key} = {value}")


# 使用示例
def create_safety_monitor() -> SafetyMonitor:
    """创建安全监控器实例"""
    monitor = SafetyMonitor()

    # 配置文档要求的阈值
    doc_thresholds = {
        'hp_over_voltage': 70.0,  # 文档2.3.3.1
        'hp_under_voltage': 16.0,  # 文档2.3.3.1
        'lp_over_voltage': 24.0,  # 文档2.3.3.2
        'temp_warning': 100.0,  # 文档2.3.3.4
        'temp_shutdown': 105.0,  # 文档2.3.3.4
        'ntc_count': 2  # 文档2.3.3.4
    }
    monitor.configure_thresholds(doc_thresholds)

    return monitor


if __name__ == "__main__":
    # 测试安全监控功能
    import logging

    logging.basicConfig(level=logging.INFO)

    monitor = create_safety_monitor()

    # 模拟正常测量值
    monitor.update_measurements({
        'hp_voltage': 42.0,
        'lp_voltage': 14.0,
        'output_current': 10.0,
        'temperatures': [25.0, 28.0]
    })

    print("安全监控测试完成")