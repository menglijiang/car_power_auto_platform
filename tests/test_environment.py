"""
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
    print("\n✅ 所有测试通过!")
