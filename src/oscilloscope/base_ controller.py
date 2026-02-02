#!/usr/bin/env python3
"""
示波器远程控制基类
提供统一的参数控制接口
"""
import pyvisa
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class TriggerType(Enum):
    """触发类型枚举"""
    EDGE = "EDGE"
    PULSE = "PULSE"
    SLOPE = "SLOPE"


class AcquisitionMode(Enum):
    """采集模式枚举"""
    NORMAL = "NORMAL"
    PEAK = "PEAK"
    AVERAGE = "AVERAGE"


@dataclass
class OscilloscopeSettings:
    """示波器参数设置"""
    timebase_scale: float = 1e-3  # 时基刻度 (s/div)
    vertical_scales: Dict[int, float] = None  # 通道:刻度 (V/div)
    trigger_level: float = 0.0  # 触发电平
    acquisition_mode: AcquisitionMode = AcquisitionMode.NORMAL


class BaseOscilloscopeController(ABC):
    """示波器控制器基类"""

    def __init__(self, resource_string: str):
        self.resource_string = resource_string
        self.instrument = None
        self.connected = False

    def connect(self) -> bool:
        """连接示波器"""
        try:
            rm = pyvisa.ResourceManager()
            self.instrument = rm.open_resource(self.resource_string)
            self.instrument.timeout = 10000
            self.connected = True
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    @abstractmethod
    def set_timebase(self, scale: float, offset: float = 0.0):
        """设置时基参数"""
        pass

    @abstractmethod
    def set_channel_parameters(self, channel: int, scale: float, offset: float = 0.0):
        """设置通道参数"""
        pass

    @abstractmethod
    def capture_waveform(self, channel: int) -> Tuple[np.ndarray, np.ndarray]:
        """捕获波形数据"""
        pass