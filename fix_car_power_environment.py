"""
汽车电源测试框架 - 环境修复脚本（增强版）
此脚本将诊断并修复PyYAML安装问题，使用ruamel.yaml替代
"""
import os
import sys
import subprocess
import platform
import logging
import shutil
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('environment_fix.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class EnvironmentFixer:
    """环境修复器类"""

    def __init__(self):
        self.project_root = os.getcwd()
        self.system_info = self.get_system_info()
        self.python_info = self.get_python_info()

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0]
        }

    def get_python_info(self) -> Dict[str, Any]:
        """获取Python信息"""
        return {
            "version": sys.version,
            "executable": sys.executable,
            "platform": sys.platform,
            "path": sys.path[:3]  # 只显示前3个路径
        }

    def print_banner(self):
        """打印横幅"""
        print("\n" + "=" * 70)
        print("汽车电源测试框架 - 环境诊断与修复工具")
        print("=" * 70)
        print(f"项目路径: {self.project_root}")
        print(f"操作系统: {self.system_info['system']} {self.system_info['release']}")
        print(f"Python路径: {self.python_info['executable']}")
        print(f"Python版本: {sys.version.split()[0]}")
        print("=" * 70 + "\n")

    def check_virtual_env(self) -> bool:
        """检查是否在虚拟环境中"""
        in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

        if in_venv:
            logger.info("✓ 检测到虚拟环境")
            return True
        else:
            logger.warning("⚠ 未检测到虚拟环境，建议在虚拟环境中运行")

            # 检查是否有常见的虚拟环境目录
            venv_dirs = ['venv', '.venv', 'env']
            for venv_dir in venv_dirs:
                if os.path.exists(venv_dir):
                    logger.info(f"发现虚拟环境目录: {venv_dir}")

                    # 检查激活脚本
                    if self.system_info['system'] == 'Windows':
                        activate_script = os.path.join(venv_dir, 'Scripts', 'activate.bat')
                    else:
                        activate_script = os.path.join(venv_dir, 'bin', 'activate')

                    if os.path.exists(activate_script):
                        logger.info(f"虚拟环境激活脚本: {activate_script}")
                        print(f"\n请先激活虚拟环境:")
                        if self.system_info['system'] == 'Windows':
                            print(f"  {venv_dir}\\Scripts\\activate")
                        else:
                            print(f"  source {venv_dir}/bin/activate")
                        print("然后重新运行此脚本。\n")
                        return False

            response = input("是否继续在全局环境中安装? (y/n): ")
            return response.lower() == 'y'

    def run_command(self, cmd: str, check: bool = True, cwd: Optional[str] = None) -> Tuple[bool, str]:
        """运行命令行命令"""
        if cwd is None:
            cwd = self.project_root

        logger.debug(f"执行命令: {cmd}")
        logger.debug(f"工作目录: {cwd}")

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd,
                encoding='utf-8',
                errors='ignore'
            )

            if result.returncode != 0:
                error_msg = f"命令执行失败 (返回码: {result.returncode}):\n"
                if result.stderr:
                    error_msg += f"错误输出:\n{result.stderr}\n"
                if result.stdout:
                    error_msg += f"标准输出:\n{result.stdout}"

                logger.error(error_msg)

                if check:
                    return False, error_msg
                else:
                    return False, result.stderr or result.stdout or ""
            else:
                logger.debug(f"命令输出: {result.stdout[:500]}")  # 只记录前500字符
                return True, result.stdout

        except Exception as e:
            error_msg = f"执行命令时发生异常: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def upgrade_pip_tools(self) -> bool:
        """升级pip、setuptools和wheel"""
        logger.info("升级pip、setuptools和wheel...")

        tools = ["pip", "setuptools", "wheel"]
        all_success = True

        for tool in tools:
            logger.info(f"正在升级 {tool}...")
            success, output = self.run_command(
                f"{sys.executable} -m pip install --upgrade {tool}",
                check=False
            )

            if success:
                logger.info(f"✓ {tool} 升级成功")
            else:
                logger.warning(f"⚠ {tool} 升级可能有问题: {output[:200]}")
                all_success = False

        return all_success

    def clean_pyyaml_installations(self) -> bool:
        """清理所有PyYAML安装"""
        logger.info("清理现有的PyYAML安装...")

        # 尝试卸载不同可能的大小写
        pyyaml_names = ["pyyaml", "PyYAML", "PyYaml"]

        for name in pyyaml_names:
            success, output = self.run_command(
                f"{sys.executable} -m pip uninstall {name} -y",
                check=False
            )

            if "not installed" not in output:
                logger.info(f"已尝试卸载: {name}")

        # 检查是否还有残留
        success, output = self.run_command(
            f"{sys.executable} -c \"import sys; exec('try:\\n import yaml\\n print(\\\"FOUND\\\" + yaml.__version__)\\nexcept:\\n print(\\\"NOT_FOUND\\\")')\"",
            check=False
        )

        if "FOUND" in output:
            logger.warning("PyYAML仍然存在，可能需要手动清理")
            return False

        logger.info("✓ PyYAML清理完成")
        return True

    def install_ruamel_yaml(self) -> bool:
        """安装ruamel.yaml作为PyYAML的替代品"""
        logger.info("安装ruamel.yaml...")

        # 尝试不同版本
        ruamel_versions = [
            "ruamel.yaml==0.17.21",  # 稳定版本
            "ruamel.yaml",  # 最新版本
            "ruamel.yaml<0.18"  # 0.17.x系列
        ]

        for version in ruamel_versions:
            logger.info(f"尝试安装: {version}")
            success, output = self.run_command(
                f"{sys.executable} -m pip install {version}",
                check=False
            )

            if success:
                logger.info(f"✓ ruamel.yaml 安装成功")

                # 验证安装
                test_success, test_output = self.run_command(
                    f"{sys.executable} -c \"from ruamel.yaml import YAML; print('IMPORT_SUCCESS')\"",
                    check=False
                )

                if test_success and "IMPORT_SUCCESS" in test_output:
                    logger.info("✓ ruamel.yaml 导入测试成功")
                    return True
                else:
                    logger.warning("ruamel.yaml 安装但导入失败，尝试下一个版本")
            else:
                logger.warning(f"安装 {version} 失败: {output[:200]}")

        logger.error("✗ 所有ruamel.yaml版本安装都失败")
        return False

    def create_minimal_requirements(self) -> bool:
        """创建最小化的requirements.txt文件"""
        logger.info("创建最小化依赖配置...")

        # 根据操作系统选择不同的依赖
        if self.system_info['system'] == 'Windows':
            # Windows上避免需要编译的包
            minimal_requirements = """# 汽车电源测试框架 - 最小依赖配置（Windows优化版）
# 测试框架核心
pytest==7.4.0
pytest-html==4.1.1

# 硬件通信（Windows版本）
pyvisa==1.13.0
pyvisa-py==0.7.0
python-can==4.2.0  # 使用较旧但稳定的版本

# 数据配置处理（使用ruamel.yaml替代pyyaml，避免编译问题）
ruamel.yaml==0.17.21

# 基础工具
colorama==0.4.6
loguru==0.7.2

# 可选：如果需要并行测试，但可能有问题
# pytest-xdist==3.3.0

# 可选：如果需要Allure报告
# allure-pytest==2.13.0
"""
        else:
            # Linux/macOS可以使用更多功能
            minimal_requirements = """# 汽车电源测试框架 - 最小依赖配置
# 测试框架
pytest==8.2.0
pytest-xdist==3.6.1
pytest-html==4.1.1
allure-pytest==2.13.0

# 硬件通信与控制
pyvisa==1.13.0
python-can==4.3.1
pyserial==3.5

# 数据处理与配置
ruamel.yaml==0.17.21
numpy==1.26.4

# 日志与工具
loguru==0.7.2
colorama==0.4.6
"""

        requirements_path = os.path.join(self.project_root, "requirements_minimal.txt")

        try:
            with open(requirements_path, "w", encoding="utf-8") as f:
                f.write(minimal_requirements)

            logger.info(f"✓ 已创建最小依赖文件: {requirements_path}")
            return True
        except Exception as e:
            logger.error(f"✗ 创建requirements_minimal.txt失败: {e}")
            return False

    def install_minimal_requirements(self) -> bool:
        """安装最小化依赖"""
        logger.info("安装最小化依赖...")

        requirements_file = "requirements_minimal.txt"

        if not os.path.exists(requirements_file):
            logger.error(f"✗ 找不到依赖文件: {requirements_file}")
            return False

        success, output = self.run_command(
            f"{sys.executable} -m pip install -r {requirements_file}",
            check=False
        )

        if success:
            logger.info("✓ 最小依赖安装成功")
        else:
            logger.warning(f"⚠ 最小依赖安装可能有问题: {output[:500]}")

        return success

    def create_project_structure(self) -> bool:
        """创建项目目录结构（如果不存在）"""
        logger.info("检查/创建项目目录结构...")

        directories = [
            "config",
            "src/drivers",
            "src/common",
            "src/system_under_test",
            "tests/unit",
            "tests/integration",
            "tests/system",
            "reports",
            "logs"
        ]

        all_success = True

        for directory in directories:
            dir_path = os.path.join(self.project_root, directory)

            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.debug(f"目录已就绪: {directory}")

                # 创建 __init__.py 文件
                if directory.startswith("src/") or directory.startswith("tests/"):
                    init_file = os.path.join(dir_path, "__init__.py")
                    if not os.path.exists(init_file):
                        with open(init_file, "w", encoding="utf-8") as f:
                            f.write(f"# {directory} 模块\n")
                        logger.debug(f"创建: {directory}/__init__.py")

            except Exception as e:
                logger.error(f"✗ 创建目录失败 {directory}: {e}")
                all_success = False

        # 创建配置文件示例
        config_example = """# 汽车电源测试配置示例
default:
  description: "默认测试配置"
  instrument_setup:
    power_supply_addr: "TCPIP0::192.168.1.100::inst0::INSTR"
    dmm_addr: "TCPIP0::192.168.1.101::inst0::INSTR"
  test_parameters:
    voltage_tolerance: 0.1
    max_current: 10.0
  safety_limits:
    over_voltage: 16.0
    over_current: 10.0
    over_temperature: 85.0
"""

        config_file = os.path.join(self.project_root, "config", "parameters.yaml")
        if not os.path.exists(config_file):
            try:
                with open(config_file, "w", encoding="utf-8") as f:
                    f.write(config_example)
                logger.info(f"✓ 创建示例配置文件: config/parameters.yaml")
            except Exception as e:
                logger.error(f"✗ 创建配置文件失败: {e}")
                all_success = False

        logger.info("✓ 项目目录结构检查完成")
        return all_success

    def create_ruamel_config_loader(self) -> bool:
        """创建ruamel.yaml配置加载器"""
        logger.info("创建ruamel.yaml配置加载器...")

        config_loader_code = '''"""
配置加载模块 - 使用ruamel.yaml
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)

class ConfigLoader:
    """配置加载器"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.yaml = YAML()
        self.yaml.indent(mapping=2, sequence=4, offset=2)

        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)

    def load_config(self, config_file: str = "parameters.yaml") -> Dict[str, Any]:
        """
        加载配置文件

        Args:
            config_file: 配置文件名

        Returns:
            配置字典
        """
        config_path = self.config_dir / config_file

        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}")
            return self._get_default_config()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = self.yaml.load(f) or {}

            logger.info(f"已加载配置文件: {config_path}")
            return config

        except Exception as e:
            logger.error(f"加载配置文件失败 {config_path}: {e}")
            return self._get_default_config()

    def save_config(self, config: Dict[str, Any], config_file: str = "parameters.yaml") -> bool:
        """
        保存配置到文件

        Args:
            config: 配置字典
            config_file: 配置文件名

        Returns:
            是否成功
        """
        config_path = self.config_dir / config_file

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                self.yaml.dump(config, f)

            logger.info(f"配置已保存: {config_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置失败 {config_path}: {e}")
            return False

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "default": {
                "instrument_setup": {
                    "power_supply_addr": "TCPIP0::192.168.1.100::inst0::INSTR",
                    "dmm_addr": "TCPIP0::192.168.1.101::inst0::INSTR"
                },
                "test_parameters": {
                    "voltage_tolerance": 0.1,
                    "max_current": 10.0
                }
            }
        }

    def get_value(self, config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """
        从配置中获取值

        Args:
            config: 配置字典
            key_path: 键路径，用点分隔，如 "default.instrument_setup.power_supply_addr"
            default: 默认值

        Returns:
            配置值或默认值
        """
        keys = key_path.split('.')
        value = config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

# 创建全局实例
_loader = ConfigLoader()

# 便捷函数
def load_config(config_file: str = "parameters.yaml") -> Dict[str, Any]:
    """加载配置的便捷函数"""
    return _loader.load_config(config_file)

def save_config(config: Dict[str, Any], config_file: str = "parameters.yaml") -> bool:
    """保存配置的便捷函数"""
    return _loader.save_config(config, config_file)

def get_config_value(key_path: str, default: Any = None, config_file: str = "parameters.yaml") -> Any:
    """获取配置值的便捷函数"""
    config = _loader.load_config(config_file)
    return _loader.get_value(config, key_path, default)
'''

        # 确保src/common目录存在
        common_dir = os.path.join(self.project_root, "src", "common")
        os.makedirs(common_dir, exist_ok=True)

        config_loader_path = os.path.join(common_dir, "config_loader.py")

        try:
            with open(config_loader_path, "w", encoding="utf-8") as f:
                f.write(config_loader_code)

            logger.info(f"✓ 配置加载器已创建: {config_loader_path}")

            # 测试配置加载器
            test_code = '''
import sys
sys.path.insert(0, '.')
from src.common.config_loader import load_config

config = load_config()
print("配置加载测试成功!")
print(f"加载的配置键: {list(config.keys())}")
'''

            test_success, test_output = self.run_command(
                f'{sys.executable} -c "{test_code}"',
                check=False
            )

            if test_success:
                logger.info("✓ 配置加载器测试通过")
            else:
                logger.warning(f"配置加载器测试失败: {test_output}")

            return test_success

        except Exception as e:
            logger.error(f"✗ 创建配置加载器失败: {e}")
            return False

    def create_simple_test(self) -> bool:
        """创建简单的测试用例"""
        logger.info("创建简单测试用例...")

        test_code = '''"""
简单测试用例 - 验证环境配置
"""
import sys
import os
import pytest

def test_environment():
    """测试环境是否正常"""
    # 检查Python版本
    assert sys.version_info >= (3, 7), "需要Python 3.7或更高版本"

    # 检查关键模块
    try:
        import pytest
        import ruamel.yaml
        print("✓ 关键模块导入成功")
    except ImportError as e:
        pytest.fail(f"模块导入失败: {e}")

    # 检查项目结构
    assert os.path.exists("config"), "缺少config目录"
    assert os.path.exists("src"), "缺少src目录"
    assert os.path.exists("tests"), "缺少tests目录"

    print("✓ 项目结构检查通过")

def test_config_loading():
    """测试配置加载"""
    try:
        # 添加src到路径
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

        from common.config_loader import load_config
        config = load_config()

        assert isinstance(config, dict), "配置应为字典类型"
        assert "default" in config, "配置应包含default节"

        print("✓ 配置加载测试通过")

    except Exception as e:
        pytest.fail(f"配置加载失败: {e}")

if __name__ == "__main__":
    # 直接运行测试
    test_environment()
    test_config_loading()
    print("\\n✅ 所有测试通过!")
'''

        test_file = os.path.join(self.project_root, "tests", "test_environment.py")

        try:
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_code)

            logger.info(f"✓ 测试用例已创建: {test_file}")
            return True
        except Exception as e:
            logger.error(f"✗ 创建测试用例失败: {e}")
            return False

    def run_environment_test(self) -> bool:
        """运行环境测试"""
        logger.info("运行环境测试...")

        test_file = os.path.join(self.project_root, "tests", "test_environment.py")

        if not os.path.exists(test_file):
            logger.error(f"✗ 测试文件不存在: {test_file}")
            return False

        success, output = self.run_command(
            f"{sys.executable} {test_file}",
            check=False
        )

        if success:
            logger.info("✓ 环境测试通过")
            if output:
                print(f"\n测试输出:\n{output}")
            return True
        else:
            logger.error(f"✗ 环境测试失败: {output}")
            return False

    def diagnose_problems(self):
        """诊断常见问题"""
        logger.info("诊断环境问题...")

        problems = []
        solutions = []

        # 检查Python版本
        if sys.version_info < (3, 7):
            problems.append("Python版本过低（需要3.7+）")
            solutions.append("升级到Python 3.7或更高版本")

        # 检查pip版本
        success, output = self.run_command(
            f"{sys.executable} -m pip --version",
            check=False
        )

        if not success:
            problems.append("pip不可用或版本过旧")
            solutions.append("运行: python -m ensurepip --upgrade")

        # 检查磁盘空间
        if self.system_info['system'] == 'Windows':
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(self.project_root[:3]),
                None, None, ctypes.pointer(free_bytes)
            )
            free_gb = free_bytes.value / (1024 ** 3)

            if free_gb < 1:
                problems.append(f"磁盘空间不足（仅剩{free_gb:.1f}GB）")
                solutions.append("清理磁盘空间，至少需要1GB空闲空间")

        # 检查网络连接
        try:
            import urllib.request
            urllib.request.urlopen("https://pypi.org", timeout=5)
        except:
            problems.append("网络连接可能有问题")
            solutions.append("检查网络连接，或使用国内镜像源: pip install -i https://pypi.tuna.tsinghua.edu.cn/simple")

        # 输出诊断结果
        if problems:
            print("\n" + "=" * 70)
            print("诊断发现问题:")
            for i, (problem, solution) in enumerate(zip(problems, solutions), 1):
                print(f"\n{i}. 问题: {problem}")
                print(f"   建议: {solution}")
            print("=" * 70)
        else:
            print("\n✓ 未发现明显问题")

        return len(problems) == 0

    def run(self) -> bool:
        """运行修复流程"""
        self.print_banner()

        # 检查虚拟环境
        if not self.check_virtual_env():
            return False

        # 诊断问题
        self.diagnose_problems()

        print("\n开始修复流程...")

        steps = [
            ("升级pip工具", self.upgrade_pip_tools),
            ("清理PyYAML安装", self.clean_pyyaml_installations),
            ("安装ruamel.yaml", self.install_ruamel_yaml),
            ("创建最小依赖配置", self.create_minimal_requirements),
            ("安装最小依赖", self.install_minimal_requirements),
            ("创建项目结构", self.create_project_structure),
            ("创建配置加载器", self.create_ruamel_config_loader),
            ("创建测试用例", self.create_simple_test),
            ("运行环境测试", self.run_environment_test)
        ]

        all_success = True
        failed_steps = []

        for step_name, step_func in steps:
            print(f"\n{'=' * 50}")
            print(f"步骤: {step_name}")
            print(f"{'=' * 50}")

            try:
                success = step_func()
                if success:
                    print(f"✓ {step_name} 完成")
                else:
                    print(f"⚠ {step_name} 可能有问题")
                    all_success = False
                    failed_steps.append(step_name)

                    # 询问是否继续
                    if step_name not in ["运行环境测试", "创建测试用例"]:
                        response = input(f"\n{step_name} 可能失败，是否继续? (y/n): ")
                        if response.lower() != 'y':
                            print("用户选择中止")
                            return False
            except Exception as e:
                print(f"✗ {step_name} 异常: {e}")
                all_success = False
                failed_steps.append(step_name)

        # 输出总结
        print("\n" + "=" * 70)
        print("修复流程完成!")
        print("=" * 70)

        if all_success:
            print("✅ 所有步骤成功完成!")
            print("\n下一步:")
            print("1. 激活虚拟环境（如果使用）")
            print("2. 运行测试: pytest tests/ -v")
            print("3. 开始开发您的电源测试用例")
        else:
            print("⚠ 部分步骤可能有问题")
            print(f"失败的步骤: {', '.join(failed_steps)}")

            print("\n建议的解决方案:")
            print("1. 确保在项目根目录运行此脚本")
            print("2. 以管理员身份运行命令提示符（Windows）")
            print("3. 检查网络连接")
            print("4. 手动运行失败的步骤")

            print("\n手动安装命令:")
            print(f"  {sys.executable} -m pip install ruamel.yaml pytest")

        print(f"\n详细日志已保存到: {os.path.join(self.project_root, 'environment_fix.log')}")
        print("=" * 70)

        return all_success


def main():
    """主函数"""
    fixer = EnvironmentFixer()

    try:
        success = fixer.run()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n用户中断")
        return 130
    except Exception as e:
        print(f"\n未处理的异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # 检查是否在项目根目录
    current_dir = os.getcwd()
    if not os.path.exists("requirements.txt") and not os.path.exists("src"):
        print(f"警告: 当前目录可能不是项目根目录")
        print(f"当前目录: {current_dir}")
        print(f"建议在包含 requirements.txt 或 src/ 目录的文件夹中运行")

        response = input("是否继续? (y/n): ")
        if response.lower() != 'y':
            print("退出")
            sys.exit(1)

    sys.exit(main())
