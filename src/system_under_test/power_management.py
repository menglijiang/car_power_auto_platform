#!/usr/bin/env python3
"""
电源管理模块 - 集成安全监控功能
符合SOR_48V电源模块技术要求_V1.0
文档参考：2.3.3故障诊断和保护、4.功能安全需求
"""
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import json

# 导入安全监控模块
from .safety_monitor import SafetyMonitor, FaultType, SafetyState

class PowerManagement:
    """
    电源管理主类 - 集成完整的安全监控系统
    负责48V电源模块的全面管理和测试
    """
    
    def __init__(self, use_simulator: bool = False, config_file: str = "config/parameters.yaml"):
        """
        初始化电源管理系统
        
        Args:
            use_simulator: 是否使用模拟器模式
            config_file: 配置文件路径
        """
        self.use_simulator = use_simulator
        self.config_file = Path(config_file)
        self.project_root = Path.cwd()
        
        # 设置日志
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 初始化状态变量
        self.is_initialized = False
        self.output_enabled = False
        self.current_mode = "BUCK"  # 默认降压模式
        self.measurements = {}
        self.fault_history = []
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化安全监控系统 - 核心集成点
        self._initialize_safety_monitor()
        
        # 初始化硬件驱动
        self._initialize_hardware_drivers()
        
        self.logger.info("电源管理系统初始化完成")
        self.is_initialized = True
    
    def _setup_logging(self):
        """设置日志系统"""
        log_dir = self.project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),  # 控制台输出
                logging.FileHandler(log_dir / 'power_management.log', encoding='utf-8')
            ]
        )
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                import yaml
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            else:
                self.logger.warning(f"配置文件不存在: {self.config_file}")
                return self._get_default_config()
        except Exception as e:
            self.logger.error(f"加载配置失败: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置 - 基于SOR文档要求"""
        return {
            "safety_thresholds": {
                # HP侧电压保护（文档2.3.3.1）
                "hp_over_voltage": 70.0,    # V_HP > 70V时过压关断
                "hp_under_voltage": 16.0,   # V_HP < 16V时欠压关断
                
                # LP侧电压保护（文档2.3.3.2）
                "lp_over_voltage": 24.0,    # V_LP > 24V时过压关断
                
                # 过流保护（文档2.3.3.3）
                "over_current_fast": 50.0,  # A (us级快速关断)
                "over_current_slow": 40.0,   # A (s级慢速关断)
                
                # 温度保护（文档2.3.3.4）
                "temp_warning": 100.0,      # °C 过温预警
                "temp_shutdown": 105.0,     # °C 过温关断
            },
            "performance_requirements": {
                # 降压模式性能（文档2.2.3）
                "buck_mode": {
                    "input_voltage_range": [18, 60],  # V
                    "output_power_25c": 1000,         # W @25°C
                    "output_power_65c": 700,          # W @65°C  
                    "output_power_85c": 600,          # W @85°C
                    "efficiency_target": 97.5        # % @500W
                },
                # 升压模式性能（文档2.2.4）
                "boost_mode": {
                    "input_voltage_range": [9, 18],   # V
                    "output_power_85c": 600           # W @85°C
                }
            },
            "test_parameters": {
                "sampling_interval": 0.1,      # 采样间隔(秒)
                "measurement_samples": 5,     # 测量样本数
                "voltage_tolerance": 0.1,     # 电压容差(10%)
                "current_tolerance": 0.05     # 电流容差(5%)
            }
        }
    
    def _initialize_safety_monitor(self):
        """初始化安全监控系统 - 核心集成方法"""
        try:
            # 创建安全监控器实例
            self.safety_monitor = SafetyMonitor()
            
            # 注册故障回调函数 - 基于文档2.3.3节要求
            self._register_fault_callbacks()
            
            # 配置安全阈值
            safety_config = self.config.get("safety_thresholds", {})
            self.safety_monitor.configure_thresholds(safety_config)
            
            # 注册状态变化回调
            self.safety_monitor.add_state_callback(self._on_safety_state_change)
            
            self.logger.info("安全监控系统初始化完成")
            
        except Exception as e:
            self.logger.error(f"安全监控初始化失败: {e}")
            raise
    
    def _register_fault_callbacks(self):
        """注册故障回调函数 - 实现文档要求的故障处理"""
        
        # HP侧过压保护回调（文档2.3.3.1）
        self.safety_monitor.add_fault_callback(
            FaultType.HP_OVERVOLTAGE, 
            self._on_hp_over_voltage
        )
        
        # HP侧欠压保护回调（文档2.3.3.1）
        self.safety_monitor.add_fault_callback(
            FaultType.HP_UNDERVOLTAGE,
            self._on_hp_under_voltage
        )
        
        # LP侧过压保护回调（文档2.3.3.2）
        self.safety_monitor.add_fault_callback(
            FaultType.LP_OVERVOLTAGE,
            self._on_lp_over_voltage
        )
        
        # 过流保护回调（文档2.3.3.3）
        self.safety_monitor.add_fault_callback(
            FaultType.OVERCURRENT,
            self._on_overcurrent
        )
        
        # 过温保护回调（文档2.3.3.4）
        self.safety_monitor.add_fault_callback(
            FaultType.OVERTEMPERATURE,
            self._on_overtemperature
        )
        
        # 通信故障回调
        self.safety_monitor.add_fault_callback(
            FaultType.COMMUNICATION_FAILURE,
            self._on_communication_failure
        )
    
    def _initialize_hardware_drivers(self):
        """初始化硬件驱动程序"""
        try:
            if self.use_simulator:
                from .power_supply_simulator import PowerSupplySimulator
                self.ps_driver = PowerSupplySimulator()
                self.logger.info("使用电源模拟器模式")
            else:
                from src.drivers.power_supply_driver import PowerSupplyDriver
                ps_addr = self.config.get("instrument_setup", {}).get("power_supply_addr")
                self.ps_driver = PowerSupplyDriver(ps_addr)
                self.logger.info(f"使用真实硬件驱动: {ps_addr}")
                
        except ImportError as e:
            self.logger.warning(f"硬件驱动导入失败，使用模拟器: {e}")
            from .power_supply_simulator import PowerSupplySimulator
            self.ps_driver = PowerSupplySimulator()
            self.use_simulator = True
    
    def _on_safety_state_change(self, new_state: SafetyState, reason: str = ""):
        """安全状态变化回调"""
        self.logger.info(f"安全状态变化: {self.safety_monitor.current_state} -> {new_state} - {reason}")
        
        if new_state == SafetyState.FAULT:
            # 故障状态，执行紧急关断
            self.emergency_shutdown(f"安全监控触发: {reason}")
        elif new_state == SafetyState.NORMAL and self.safety_monitor.current_state == SafetyState.FAULT:
            # 从故障恢复
            self.logger.info("系统从故障状态恢复正常")
    
    def _on_hp_over_voltage(self, fault_info: Dict):
        """HP侧过压故障处理（文档2.3.3.1）"""
        self.logger.error(f"HP侧过压故障: {fault_info}")
        self.emergency_shutdown("HP侧过压保护触发")
        
    def _on_hp_under_voltage(self, fault_info: Dict):
        """HP侧欠压故障处理（文档2.3.3.1）"""
        self.logger.error(f"HP侧欠压故障: {fault_info}")
        self.emergency_shutdown("HP侧欠压保护触发")
    
    def _on_lp_over_voltage(self, fault_info: Dict):
        """LP侧过压故障处理（文档2.3.3.2）"""
        self.logger.error(f"LP侧过压故障: {fault_info}")
        self.emergency_shutdown("LP侧过压保护触发")
    
    def _on_overcurrent(self, fault_info: Dict):
        """过流故障处理（文档2.3.3.3）"""
        fault_type = fault_info.get('description', '')
        self.logger.error(f"过流故障[{fault_type}]: {fault_info}")
        
        if "快速" in fault_type:
            # us级快速关断
            self.emergency_shutdown("快速过流保护触发", immediate=True)
        else:
            # s级慢速关断
            self.emergency_shutdown("慢速过流保护触发")
    
    def _on_overtemperature(self, fault_info: Dict):
        """过温故障处理（文档2.3.3.4）"""
        self.logger.error(f"过温故障: {fault_info}")
        self.emergency_shutdown("过温保护触发")
        
        # 过温保护需要EN重使能恢复（文档要求）
        self.requires_en_restart = True
    
    def _on_communication_failure(self, fault_info: Dict):
        """通信故障处理"""
        self.logger.error(f"通信故障: {fault_info}")
        self.emergency_shutdown("通信故障")
    
    def enable_output(self, enable: bool = True) -> bool:
        """
        启用/禁用输出
        文档参考：2.3.2启动需求
        """
        try:
            if not self.is_initialized:
                self.logger.error("系统未初始化")
                return False
            
            success = self.ps_driver.enable_output(enable)
            
            if success:
                self.output_enabled = enable
                state = "启用" if enable else "禁用"
                self.logger.info(f"输出{state}成功")
                
                # 记录启动时间（文档要求<40ms）
                if enable:
                    self.startup_time = time.time()
                    self.logger.info("开始记录启动时间")
            else:
                self.logger.error(f"输出{'启用' if enable else '禁用'}失败")
            
            return success
            
        except Exception as e:
            self.logger.error(f"设置输出状态失败: {e}")
            return False
    
    def set_voltage(self, voltage: float, channel: int = 1) -> bool:
        """
        设置输出电压
        文档参考：2.2.3降压稳态性能要求
        """
        try:
            # 安全检查
            if not self._safety_check_before_operation():
                return False
            
            success = self.ps_driver.set_voltage(voltage, channel)
            
            if success:
                self.logger.info(f"设置电压成功: {voltage}V")
                
                # 更新测量值并通知安全监控
                self._update_measurements()
            else:
                self.logger.error(f"设置电压失败: {voltage}V")
            
            return success
            
        except Exception as e:
            self.logger.error(f"设置电压异常: {e}")
            return False
    
    def set_current_limit(self, current: float, channel: int = 1) -> bool:
        """
        设置电流限制
        文档参考：2.2.3性能要求
        """
        try:
            success = self.ps_driver.set_current_limit(current, channel)
            
            if success:
                self.logger.info(f"设置电流限制成功: {current}A")
            else:
                self.logger.error(f"设置电流限制失败: {current}A")
            
            return success
            
        except Exception as e:
            self.logger.error(f"设置电流限制异常: {e}")
            return False
    
    def measure_parameters(self) -> Dict[str, float]:
        """
        测量关键参数
        返回：电压、电流、温度等测量值
        """
        try:
            measurements = {
                'timestamp': time.time(),
                'hp_voltage': self.ps_driver.measure_voltage(1),  # HP侧电压
                'lp_voltage': self.ps_driver.measure_voltage(2),  # LP侧电压
                'output_current': self.ps_driver.measure_current(1),
                'temperatures': self._read_temperatures()  # 2个NTC温度
            }
            
            # 更新安全监控
            self.safety_monitor.update_measurements(measurements)
            
            # 保存测量记录
            self.measurements = measurements
            self._record_measurement(measurements)
            
            return measurements
            
        except Exception as e:
            self.logger.error(f"测量参数失败: {e}")
            return {}
    
    def _read_temperatures(self) -> List[float]:
        """读取温度值 - 模拟2个NTC温度传感器（文档2.3.3.4要求）"""
        try:
            # 模拟温度读取 - 实际应通过硬件接口读取
            if self.use_simulator:
                import random
                base_temp = 25.0
                if self.output_enabled:
                    # 带载时温度升高
                    base_temp += random.uniform(10, 30)
                return [base_temp + random.uniform(-2, 2) for _ in range(2)]
            else:
                # 实际硬件温度读取
                # 这里应该调用真实的温度传感器驱动
                return [25.0, 25.0]  # 默认值
        except Exception as e:
            self.logger.error(f"读取温度失败: {e}")
            return [0.0, 0.0]
    
    def _update_measurements(self):
        """更新测量值并通知安全监控"""
        measurements = self.measure_parameters()
        self.safety_monitor.update_measurements(measurements)
    
    def _safety_check_before_operation(self) -> bool:
        """操作前安全检查"""
        if not self.is_initialized:
            self.logger.error("系统未初始化")
            return False
        
        if self.safety_monitor.current_state == SafetyState.FAULT:
            self.logger.error("系统处于故障状态，禁止操作")
            return False
        
        return True
    
    def emergency_shutdown(self, reason: str = "紧急关断", immediate: bool = False):
        """
        紧急关断功能
        文档参考：2.3.3故障诊断和保护
        """
        try:
            self.logger.warning(f"执行紧急关断: {reason}")
            
            # 立即关断输出
            if immediate:
                self.ps_driver.enable_output(False)
            else:
                # 安全关断流程
                self._safe_shutdown_sequence()
            
            self.output_enabled = False
            
            # 记录故障
            fault_record = {
                'timestamp': time.time(),
                'reason': reason,
                'measurements': self.measurements.copy(),
                'state': 'SHUTDOWN'
            }
            self.fault_history.append(fault_record)
            
            self.logger.info("紧急关断完成")
            
        except Exception as e:
            self.logger.error(f"紧急关断失败: {e}")
    
    def _safe_shutdown_sequence(self):
        """安全关断序列"""
        # 1. 先降低电流限制
        self.ps_driver.set_current_limit(0.1)  # 降到最小电流
        time.sleep(0.01)
        
        # 2. 关断输出
        self.ps_driver.enable_output(False)
        
        # 3. 记录关断状态
        self.output_enabled = False
    
    def perform_startup_test(self) -> Dict[str, Any]:
        """
        执行启动测试
        文档参考：2.3.2启动需求
        """
        test_results = {
            'test_name': '启动测试',
            'timestamp': time.time(),
            'steps': [],
            'success': False
        }
        
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 步骤1: 使能模块
            test_results['steps'].append({
                'step': 1, 'action': '使能模块', 'status': '开始'
            })
            
            self.enable_output(True)
            time.sleep(0.001)  # 1ms延迟
            
            # 步骤2: 检查启动时间（文档要求<40ms）
            enable_time = time.time()
            startup_duration = (enable_time - start_time) * 1000  # 转换为ms
            
            test_results['startup_time_ms'] = startup_duration
            test_results['steps'].append({
                'step': 2, 'action': '测量启动时间', 
                'value': f'{startup_duration:.2f}ms',
                'status': 'PASS' if startup_duration < 40 else 'FAIL'
            })
            
            # 步骤3: 检查输出电压
            measurements = self.measure_parameters()
            output_voltage = measurements.get('lp_voltage', 0)
            target_voltage = 14.0  # 目标输出电压
            
            voltage_error = abs(output_voltage - target_voltage) / target_voltage
            test_results['voltage_accuracy'] = f'{(1-voltage_error)*100:.1f}%'
            
            test_results['steps'].append({
                'step': 3, 'action': '检查输出电压',
                'value': f'{output_voltage:.2f}V',
                'status': 'PASS' if voltage_error < 0.1 else 'FAIL'  # 10%容差
            })
            
            # 总体结果
            test_results['success'] = (
                startup_duration < 40 and 
                voltage_error < 0.1 and
                self.safety_monitor.current_state == SafetyState.NORMAL
            )
            
            test_results['final_result'] = 'PASS' if test_results['success'] else 'FAIL'
            
            self.logger.info(f"启动测试完成: {test_results['final_result']}")
            
        except Exception as e:
            test_results['error'] = str(e)
            test_results['final_result'] = 'ERROR'
            self.logger.error(f"启动测试失败: {e}")
        
        return test_results
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态摘要"""
        safety_status = self.safety_monitor.get_safety_status()
        
        return {
            'timestamp': time.time(),
            'initialized': self.is_initialized,
            'output_enabled': self.output_enabled,
            'current_mode': self.current_mode,
            'safety_state': safety_status['current_state'],
            'fault_count': safety_status['fault_count'],
            'current_measurements': safety_status['current_measurements'],
            'uptime': safety_status['uptime'],
            'use_simulator': self.use_simulator
        }
    
    def _record_measurement(self, measurements: Dict):
        """记录测量数据"""
        # 这里可以添加数据记录逻辑，如保存到文件或数据库
        pass
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.output_enabled:
                self.enable_output(False)
            
            self.logger.info("电源管理系统清理完成")
            
        except Exception as e:
            self.logger.error(f"清理过程中出错: {e}")
    
    def __del__(self):
        """析构函数"""
        self.cleanup()

# 使用示例
if __name__ == "__main__":
    # 创建电源管理实例（模拟器模式）
    pm = PowerManagement(use_simulator=True)
    
    try:
        # 获取系统状态
        status = pm.get_system_status()
        print("系统状态:", status)
        
        # 执行启动测试
        test_result = pm.perform_startup_test()
        print("启动测试结果:", test_result)
        
    finally:
        pm.cleanup()