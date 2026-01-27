#!/usr/bin/env python3
"""
GitHub连接诊断工具
用于诊断和解决Git推送失败的网络连接问题
"""
import os
import sys
import subprocess
import socket
import urllib.request
import time
from datetime import datetime
import json


class GitHubConnectionDiagnoser:
    """GitHub连接诊断器"""

    def __init__(self, github_username="menglijiang", repo_name="car_power_auto_platform"):
        self.github_username = github_username
        self.repo_name = repo_name
        self.https_url = f"https://github.com/{github_username}/{repo_name}.git"
        self.ssh_url = f"git@github.com:{github_username}/{repo_name}.git"
        self.diagnosis_results = {}

    def run_test(self, test_name, test_func):
        """运行测试并记录结果"""
        print(f"\n🔍 测试: {test_name}")
        print("-" * 50)

        try:
            result = test_func()
            self.diagnosis_results[test_name] = {
                "status": "PASS" if result else "FAIL",
                "timestamp": datetime.now().isoformat()
            }
            return result
        except Exception as e:
            self.diagnosis_results[test_name] = {
                "status": "ERROR",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(f"❌ 错误: {e}")
            return False

    def test_network_connectivity(self):
        """测试基本网络连接"""
        print("1. 测试互联网连接...")
        try:
            # 测试DNS解析
            socket.gethostbyname("github.com")
            print("   ✓ DNS解析正常")
        except socket.gaierror:
            print("   ✗ DNS解析失败")
            return False

        # 测试HTTP连接
        try:
            response = urllib.request.urlopen("http://www.baidu.com", timeout=5)
            if response.status == 200:
                print("   ✓ 互联网访问正常")
                return True
        except:
            print("   ✗ 互联网访问失败")

        return False

    def test_github_connection(self):
        """测试GitHub连接"""
        print("2. 测试GitHub连接...")

        # 测试HTTPS端口
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(5)

        try:
            test_socket.connect(("github.com", 443))
            print("   ✓ GitHub HTTPS端口(443)可访问")
            test_socket.close()
        except:
            print("   ✗ GitHub HTTPS端口(443)无法访问")
            return False

        # 测试SSH端口
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(5)
            test_socket.connect(("github.com", 22))
            print("   ✓ GitHub SSH端口(22)可访问")
            test_socket.close()
        except:
            print("   ✗ GitHub SSH端口(22)无法访问")

        return True

    def test_git_config(self):
        """测试Git配置"""
        print("3. 检查Git配置...")

        config_checks = [
            ("user.name", "用户名"),
            ("user.email", "邮箱"),
            ("remote.origin.url", "远程仓库URL"),
        ]

        all_passed = True

        for config_key, description in config_checks:
            try:
                result = subprocess.run(
                    ["git", "config", "--get", config_key],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode == 0:
                    value = result.stdout.strip()
                    print(f"   ✓ {description}: {value}")
                else:
                    print(f"   ✗ {description}: 未配置")
                    all_passed = False
            except:
                print(f"   ✗ 检查{description}失败")
                all_passed = False

        return all_passed

    def test_git_remote(self):
        """测试远程仓库配置"""
        print("4. 检查远程仓库...")

        try:
            # 检查远程仓库列表
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                print("   远程仓库配置:")
                for line in result.stdout.strip().split('\n'):
                    if line:
                        print(f"     {line}")

                # 检查特定远程仓库
                if "origin" in result.stdout:
                    return True
                else:
                    print("   ✗ 未找到origin远程仓库")
                    return False
            else:
                print("   ✗ 获取远程仓库失败")
                return False

        except Exception as e:
            print(f"   ✗ 检查远程仓库失败: {e}")
            return False

    def test_git_push(self, use_ssh=False):
        """测试Git推送"""
        print("5. 测试Git推送...")

        # 先尝试获取远程信息
        try:
            fetch_result = subprocess.run(
                ["git", "fetch", "--dry-run"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if fetch_result.returncode == 0:
                print("   ✓ Git fetch测试成功")
                return True
            else:
                print(f"   ✗ Git fetch失败: {fetch_result.stderr[:200]}")
                return False

        except subprocess.TimeoutExpired:
            print("   ✗ Git操作超时")
            return False
        except Exception as e:
            print(f"   ✗ Git操作异常: {e}")
            return False

    def check_proxy_settings(self):
        """检查代理设置"""
        print("6. 检查代理设置...")

        env_vars = ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]
        git_configs = ["http.proxy", "https.proxy"]

        has_proxy = False

        # 检查环境变量
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                print(f"   环境变量 {var}: {value}")
                has_proxy = True

        # 检查Git配置
        for config in git_configs:
            try:
                result = subprocess.run(
                    ["git", "config", "--get", config],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"   Git配置 {config}: {result.stdout.strip()}")
                    has_proxy = True
            except:
                pass

        if not has_proxy:
            print("   未检测到代理设置")

        return has_proxy

    def diagnose_connection_issue(self):
        """执行完整的连接诊断"""
        print("=" * 60)
        print("GitHub连接问题诊断")
        print("=" * 60)

        tests = [
            ("网络连接测试", self.test_network_connectivity),
            ("GitHub连接测试", self.test_github_connection),
            ("Git配置检查", self.test_git_config),
            ("远程仓库检查", self.test_git_remote),
            ("代理设置检查", self.check_proxy_settings),
            ("Git推送测试", lambda: self.test_git_push(use_ssh=False)),
        ]

        all_passed = True
        for test_name, test_func in tests:
            if not self.run_test(test_name, test_func):
                all_passed = False

        return all_passed

    def generate_report(self):
        """生成诊断报告"""
        report = {
            "diagnosis_time": datetime.now().isoformat(),
            "github_username": self.github_username,
            "repository": self.repo_name,
            "results": self.diagnosis_results,
            "summary": {
                "total_tests": len(self.diagnosis_results),
                "passed_tests": sum(1 for r in self.diagnosis_results.values()
                                    if r.get("status") == "PASS"),
                "failed_tests": sum(1 for r in self.diagnosis_results.values()
                                    if r.get("status") == "FAIL"),
                "error_tests": sum(1 for r in self.diagnosis_results.values()
                                   if r.get("status") == "ERROR"),
            }
        }

        return report

    def print_solutions(self, diagnosis_passed):
        """根据诊断结果提供解决方案"""
        print("\n" + "=" * 60)
        print("解决方案建议")
        print("=" * 60)

        if diagnosis_passed:
            print("🎉 所有基础测试通过！")
            print("\n💡 推送解决方案:")
            print("1. 直接运行推送命令:")
            print("   git push -u origin main")
            print("\n2. 如果还是失败，可以尝试:")
            print("   - 使用SSH协议:")
            print("     git remote set-url origin git@github.com:menglijiang/car_power_auto_platform.git")
            print("     git push -u origin main")
        else:
            print("🔧 检测到连接问题，请尝试以下解决方案:")
            print("\n方案1: 检查网络连接")
            print("   - 确保您可以访问 https://github.com")
            print("   - 尝试 ping github.com")
            print("   - 检查防火墙设置")

            print("\n方案2: 使用SSH协议替代HTTPS")
            print("   1. 生成SSH密钥: ssh-keygen -t rsa -b 4096 -C \"your_email@example.com\"")
            print("   2. 添加SSH密钥到GitHub")
            print("   3. 修改远程仓库URL:")
            print("      git remote set-url origin git@github.com:menglijiang/car_power_auto_platform.git")
            print("   4. 重新推送: git push -u origin main")

            print("\n方案3: 检查代理设置")
            print("   - 清除可能的代理设置:")
            print("     git config --global --unset http.proxy")
            print("     git config --global --unset https.proxy")

            print("\n方案4: 手动创建GitHub仓库")
            print("   1. 访问 https://github.com/new")
            print("   2. 创建名为 'car_power_auto_platform' 的仓库")
            print("   3. 不要初始化README、.gitignore或license")
            print("   4. 按照页面上的指示推送现有仓库")

            print("\n方案5: 使用GitHub CLI（如果已安装）")
            print("   gh repo create car_power_auto_platform --private --source=. --remote=origin --push")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub连接诊断工具")
    parser.add_argument("--username", default="menglijiang", help="GitHub用户名")
    parser.add_argument("--repo", default="car_power_auto_platform", help="仓库名称")

    args = parser.parse_args()

    diagnoser = GitHubConnectionDiagnoser(args.username, args.repo)

    # 运行诊断
    diagnosis_passed = diagnoser.diagnose_connection_issue()

    # 生成报告
    report = diagnoser.generate_report()

    # 保存报告
    report_file = "github_connection_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n📄 诊断报告已保存到: {report_file}")

    # 显示解决方案
    diagnoser.print_solutions(diagnosis_passed)

    # 最终状态
    print("\n" + "=" * 60)
    print("当前Git状态:")
    subprocess.run(["git", "status"], timeout=5)
    print("\n" + "=" * 60)

    if diagnosis_passed:
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
