#!/usr/bin/env python3
"""
汽车电源测试框架 - 专业版Git仓库设置工具
优化终端界面，提供清晰、专业的操作体验
"""
import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import Tuple, Dict, Optional
import textwrap
from datetime import datetime


class ConsoleFormatter:
    """控制台格式化类 - 提供专业的终端输出"""

    # Unicode符号和颜色定义
    SYMBOLS = {
        'success': '✓',
        'error': '✗',
        'warning': '⚠',
        'info': 'ℹ',
        'arrow': '➤',
        'dot': '•',
        'check': '✔',
        'cross': '✖',
        'bullet': '●',
        'empty': '○'
    }

    COLORS = {
        'success': '\033[92m',  # 绿色
        'error': '\033[91m',  # 红色
        'warning': '\033[93m',  # 黄色
        'info': '\033[94m',  # 蓝色
        'header': '\033[95m',  # 紫色
        'step': '\033[96m',  # 青色
        'reset': '\033[0m'  # 重置
    }

    @classmethod
    def print_header(cls, title: str, width: int = 60):
        """打印标题头"""
        print("\n" + "=" * width)
        print(f"{cls.COLORS['header']}{title.center(width)}{cls.COLORS['reset']}")
        print("=" * width)

    @classmethod
    def print_step(cls, step_num: int, total_steps: int, description: str):
        """打印步骤信息"""
        print(f"\n{cls.COLORS['step']}[步骤 {step_num:2d}/{total_steps:2d}] {description}{cls.COLORS['reset']}")

    @classmethod
    def print_status(cls, message: str, status: str = "info", indent: int = 2):
        """打印状态消息"""
        symbol = cls.SYMBOLS.get(status, '')
        color = cls.COLORS.get(status, cls.COLORS['info'])

        indent_str = " " * indent
        wrapped_msg = textwrap.fill(
            f"{indent_str}{color}{symbol} {message}{cls.COLORS['reset']}",
            width=80,
            subsequent_indent=indent_str + "  "
        )
        print(wrapped_msg)

    @classmethod
    def print_result(cls, success: bool, message: str = ""):
        """打印结果"""
        if success:
            print(f"  {cls.COLORS['success']}{cls.SYMBOLS['success']} 完成{cls.COLORS['reset']}", end="")
            if message:
                print(f" - {message}")
            else:
                print()
        else:
            print(f"  {cls.COLORS['error']}{cls.SYMBOLS['error']} 失败{cls.COLORS['reset']}")

    @classmethod
    def print_summary_table(cls, results: Dict[str, bool]):
        """打印摘要表格"""
        print(f"\n{cls.COLORS['header']}{'操作摘要':^60}{cls.COLORS['reset']}")
        print("-" * 60)

        for step, success in results.items():
            status = f"{cls.COLORS['success']}成功{cls.COLORS['reset']}" if success else f"{cls.COLORS['error']}失败{cls.COLORS['reset']}"
            symbol = cls.SYMBOLS['check'] if success else cls.SYMBOLS['cross']
            print(f"  {symbol} {step:<40} [{status}]")

        print("-" * 60)

    @classmethod
    def print_progress_bar(cls, current: int, total: int, length: int = 40):
        """打印进度条"""
        percent = current / total
        filled = int(length * percent)
        bar = "█" * filled + "░" * (length - filled)
        print(f"\r  [{bar}] {percent:.0%}", end="", flush=True)

    @classmethod
    def disable_colors(cls):
        """禁用颜色输出（用于不支持颜色的终端）"""
        cls.COLORS = {k: '' for k in cls.COLORS}


class GitManager:
    """Git仓库管理器 - 专业版本"""

    def __init__(self, username: str, repo_name: str, project_path: Path):
        self.username = username
        self.repo_name = repo_name
        self.project_path = project_path
        self.results = {}

        # 检测是否支持颜色
        if sys.platform == "win32":
            ConsoleFormatter.disable_colors()

    def run_command(self, cmd: str, description: str = "", show_output: bool = False) -> Tuple[bool, str]:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )

            success = result.returncode == 0
            output = result.stdout.strip() or result.stderr.strip()

            if description:
                self.results[description] = success

            if show_output and output:
                lines = output.split('\n')
                for line in lines[:3]:  # 只显示前3行输出
                    if line.strip():
                        print(f"      {ConsoleFormatter.SYMBOLS['arrow']} {line}")
                if len(lines) > 3:
                    print(f"      ... 还有 {len(lines) - 3} 行输出")

            return success, output

        except subprocess.TimeoutExpired:
            ConsoleFormatter.print_status("命令执行超时", "error")
            return False, "命令执行超时"
        except Exception as e:
            ConsoleFormatter.print_status(f"执行异常: {e}", "error")
            return False, str(e)

    def check_git_installation(self) -> bool:
        """检查Git安装"""
        ConsoleFormatter.print_status("验证Git安装")
        success, output = self.run_command("git --version", "检查Git安装")

        if success:
            version = output.split()[-1] if output else "未知版本"
            ConsoleFormatter.print_result(True, f"版本: {version}")
        else:
            ConsoleFormatter.print_result(False)

        return success

    def initialize_repository(self) -> bool:
        """初始化仓库"""
        ConsoleFormatter.print_status("初始化Git仓库")

        git_dir = self.project_path / ".git"
        if git_dir.exists():
            ConsoleFormatter.print_status("Git仓库已存在", "warning")
            ConsoleFormatter.print_result(True, "跳过初始化")
            return True

        success, output = self.run_command("git init", "初始化仓库")
        ConsoleFormatter.print_result(success)
        return success

    def configure_user(self) -> bool:
        """配置用户信息"""
        ConsoleFormatter.print_status("配置Git用户")

        # 设置用户名
        name_success, _ = self.run_command(f'git config user.name "{self.username}"')

        # 设置邮箱
        email = f"{self.username}@users.noreply.github.com"
        email_success, _ = self.run_command(f'git config user.email "{email}"')

        success = name_success and email_success
        ConsoleFormatter.print_result(success, f"用户: {self.username}")
        return success

    def setup_remote(self) -> bool:
        """设置远程仓库"""
        ConsoleFormatter.print_status("配置远程仓库")

        remote_url = f"https://github.com/{self.username}/{self.repo_name}.git"

        # 检查是否已配置远程仓库
        success, output = self.run_command("git remote -v")
        if success and "origin" in output:
            ConsoleFormatter.print_status("远程仓库已配置", "info")
            ConsoleFormatter.print_result(True, "跳过配置")
            return True

        # 添加远程仓库
        success, output = self.run_command(f"git remote add origin {remote_url}", "添加远程仓库")

        if success:
            ConsoleFormatter.print_result(True, f"URL: {remote_url}")
        else:
            ConsoleFormatter.print_result(False)

        return success

    def add_and_commit_files(self) -> bool:
        """添加并提交文件"""
        ConsoleFormatter.print_status("提交代码变更")

        # 检查是否有文件可提交
        success, output = self.run_command("git status --porcelain")
        if not success or not output.strip():
            ConsoleFormatter.print_status("没有检测到变更", "info")
            ConsoleFormatter.print_result(True, "无需提交")
            return True

        # 计算文件数量
        file_count = len([line for line in output.strip().split('\n') if line.strip()])

        # 添加所有文件
        ConsoleFormatter.print_status(f"添加 {file_count} 个文件")
        add_success, _ = self.run_command("git add .")

        if not add_success:
            ConsoleFormatter.print_result(False)
            return False

        # 提交文件
        commit_msg = f"""初始提交: 汽车电源自动化测试框架

- 电源管理模块
- 安全监控系统
- 测试配置文件
- 完整的测试用例"""

        commit_success, _ = self.run_command(f'git commit -m "{commit_msg}"')

        if commit_success:
            ConsoleFormatter.print_result(True, f"提交了 {file_count} 个文件")
        else:
            ConsoleFormatter.print_result(False)

        return commit_success

    def push_to_remote(self, retries: int = 3) -> bool:
        """推送到远程仓库"""
        ConsoleFormatter.print_status("推送到GitHub仓库")

        for attempt in range(retries):
            if attempt > 0:
                ConsoleFormatter.print_status(f"重试推送 ({attempt}/{retries})", "warning")

            success, output = self.run_command(
                "git push -u origin main",
                "推送代码",
                show_output=True
            )

            if success:
                ConsoleFormatter.print_result(True, "推送成功")
                return True

            time.sleep(2)  # 重试前等待

        ConsoleFormatter.print_result(False)
        ConsoleFormatter.print_status("推送失败，请检查:", "error")
        ConsoleFormatter.print_status("1. 确保GitHub仓库已创建", "info")
        ConsoleFormatter.print_status("2. 检查网络连接", "info")
        ConsoleFormatter.print_status(f"3. 手动创建: https://github.com/new", "info")

        return False

    def get_repository_info(self) -> Dict:
        """获取仓库信息"""
        info = {
            "timestamp": datetime.now().isoformat(),
            "username": self.username,
            "repository": self.repo_name,
            "results": self.results.copy()
        }

        # 添加Git配置信息
        for key in ["user.name", "user.email", "remote.origin.url"]:
            success, value = self.run_command(f"git config --get {key}")
            if success:
                info[key] = value

        return info

    def save_report(self, info: Dict):
        """保存报告"""
        report_file = self.project_path / "git_setup_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False, default=str)

        ConsoleFormatter.print_status(f"报告已保存: {report_file.name}", "info")


def main():
    """主函数"""
    ConsoleFormatter.print_header("汽车电源测试框架 - Git仓库设置")

    # 获取项目信息
    project_path = Path.cwd()
    print(f"📁 项目路径: {project_path}")

    # 获取GitHub信息
    print("\n" + "=" * 60)
    print("请输入GitHub配置信息:")
    print("-" * 60)

    username = input("GitHub用户名: ").strip()
    if not username:
        ConsoleFormatter.print_status("必须提供用户名", "error")
        return 1

    repo_name = input("仓库名称 [car_power_auto_platform]: ").strip()
    if not repo_name:
        repo_name = "car_power_auto_platform"

    # 创建管理器
    manager = GitManager(username, repo_name, project_path)

    # 定义执行步骤
    steps = [
        ("检查Git安装", manager.check_git_installation),
        ("初始化仓库", manager.initialize_repository),
        ("配置用户", manager.configure_user),
        ("设置远程", manager.setup_remote),
        ("提交代码", manager.add_and_commit_files),
        ("推送代码", manager.push_to_remote),
    ]

    # 执行步骤
    print("\n" + "=" * 60)
    print("开始执行Git仓库设置...")
    print("=" * 60)

    for i, (desc, func) in enumerate(steps, 1):
        ConsoleFormatter.print_step(i, len(steps), desc)

        # 显示进度条
        if hasattr(ConsoleFormatter, 'print_progress_bar'):
            ConsoleFormatter.print_progress_bar(i - 1, len(steps))

        # 执行步骤
        try:
            success = func()
            if not success and desc != "推送代码":  # 推送可能失败，但其他步骤必须成功
                ConsoleFormatter.print_status("关键步骤失败，终止执行", "error")
                return 1
        except Exception as e:
            ConsoleFormatter.print_status(f"执行异常: {e}", "error")
            return 1

    # 完成进度条
    if hasattr(ConsoleFormatter, 'print_progress_bar'):
        ConsoleFormatter.print_progress_bar(len(steps), len(steps))
        print()  # 换行

    # 保存报告
    ConsoleFormatter.print_header("设置完成")
    repo_info = manager.get_repository_info()
    manager.save_report(repo_info)

    # 打印摘要
    ConsoleFormatter.print_summary_table(manager.results)

    # 最终信息
    print("\n" + "=" * 60)
    print(f"📁 本地仓库: {project_path}")
    print(f"🌐 远程仓库: https://github.com/{username}/{repo_name}")

    if manager.results.get("推送代码", False):
        print("\n🎉 恭喜！代码已成功推送到GitHub！")
    else:
        print("\n⚠️  代码已提交到本地，但需要手动推送到GitHub")
        print("   请运行: git push -u origin main")

    print("\n📋 后续操作:")
    print("  1. 创建新分支: git checkout -b feature/新功能")
    print("  2. 提交更改: git add . && git commit -m '描述'")
    print("  3. 推送分支: git push origin feature/新功能")
    print("  4. 在GitHub创建Pull Request")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{ConsoleFormatter.COLORS['warning']}操作被用户中断{ConsoleFormatter.COLORS['reset']}")
        sys.exit(130)
    except Exception as e:
        ConsoleFormatter.print_status(f"程序出错: {e}", "error")
        sys.exit(1)