import sys
import os

# 获取项目根目录的绝对路径
project_root = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到sys.path的最前面
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 你原有的conftest.py代码继续写在这里...
# conftest.py
import pytest
from src.system_under_test.power_management import PowerManagement

@pytest.fixture(scope="module")
def power_system():
    """初始化电源系统，整个测试模块共享一个实例"""
    system = PowerManagement("[电源地址]", "[万用表地址]")
    yield system
    # 测试结束后，自动清理，确保电源关闭
    system.ps_driver.enable_output(False)