#!/usr/bin/env python3
"""
汽车电源测试框架 - Git仓库设置工具
专业版：提供完整的Git仓库初始化、配置和推送功能
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Optional


class GitSetupManager:
    """Git仓库设置管理器"""

    def __init__(self, project_path: Path, github_username: str, repo_name: str):
        self.project_path = project_path
        self.github_username = github_username
        self.repo_name = repo_name
        self.remote_url = f"https://github.com/{github_username}/{repo_name}.git"
        self.results = {}

    def run_command(self, command: str, description: str = "") -> Tuple[bool, str]:
        """运行命令并返回结果"""
        try:
            result = subprocess.run(
                command,
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

            return success, output
        except Exception as e:
            return False, str(e)

    def check_git_installation(self) -> bool:
        """检查Git是否安装"""
        print("1. 检查Git安装...")
        success, output = self.run_command("git --version", "Git安装检查")
        if success:
            version = output.split()[-1] if output else "未知"
            print(f"   ✓ Git版本: {version}")
        else:
            print("   ✗ Git未安装或不可用")
        return success

    def initialize_repository(self) -> bool:
        """初始化Git仓库"""
        print("2. 初始化Git仓库...")

        # 检查是否已是Git仓库
        git_dir = self.project_path / ".git"
        if git_dir.exists():
            print("   ✓ Git仓库已存在")
            return True

        success, output = self.run_command("git init", "仓库初始化")
        if success:
            print("   ✓ 仓库初始化成功")
        else:
            print(f"   ✗ 初始化失败: {output}")
        return success

    def configure_user_info(self) -> bool:
        """配置用户信息"""
        print("3. 配置Git用户信息...")

        # 设置用户名
        name_success, _ = self.run_command(
            f'git config user.name "{self.github_username}"',
            "用户名配置"
        )

        # 设置邮箱
        email = f"{self.github_username}@users.noreply.github.com"
        email_success, _ = self.run_command(
            f'git config user.email "{email}"',
            "邮箱配置"
        )

        success = name_success and email_success
        if success:
            print("   ✓ 用户信息配置成功")
        else:
            print("   ✗ 用户信息配置失败")
        return success

    def setup_remote_repository(self) -> bool:
        """设置远程仓库"""
        print("4. 配置远程仓库...")

        # 检查是否已配置远程仓库
        success, output = self.run_command("git remote -v", "远程仓库检查")
        if success and "origin" in output:
            print("   ✓ 远程仓库已配置")
            return True

        # 添加远程仓库
        success, output = self.run_command(
            f"git remote add origin {self.remote_url}",
            "远程仓库添加"
        )

        if success:
            print("   ✓ 远程仓库配置成功")
        else:
            print(f"   ✗ 远程仓库配置失败: {output}")
        return success

    def add_and_commit_files(self) -> bool:
        """添加并提交文件"""
        print("5. 提交代码文件...")

        # 检查是否有文件可提交
        success, output = self.run_command("git status --porcelain", "文件状态检查")
        if not success or not output.strip():
            print("   ℹ 没有检测到文件变更")
            return True

        # 计算文件数量
        file_count = len([line for line in output.strip().split('\n') if line.strip()])

        # 添加所有文件
        add_success, _ = self.run_command("git add .", "文件添加")
        if not add_success:
            print("   ✗ 文件添加失败")
            return False

        # 提交文件
        commit_message = """初始提交: 汽车电源自动化测试框架

- 电源管理模块
- 安全监控系统  
- 测试配置文件
- 依赖检查脚本
- 完整的测试用例
- 符合SOR文档V1.0技术要求"""

        commit_success, _ = self.run_command(
            f'git commit -m "{commit_message}"',
            "代码提交"
        )

        if commit_success:
            print(f"   ✓ 提交成功 ({file_count} 个文件)")
        else:
            print("   ✗ 提交失败")
        return commit_success

    def push_to_github(self, retries: int = 3) -> bool:
        """推送到GitHub"""
        print("6. 推送到GitHub...")

        for attempt in range(retries):
            if attempt > 0:
                print(f"   重试推送 ({attempt}/{retries})...")
                time.sleep(2)

            success, output = self.run_command(
                "git push -u origin main",
                "代码推送"
            )

            if success:
                print("   ✓ 推送成功")
                return True
            else:
                print(f"   推送失败: {output}")

        print("   ✗ 推送失败，请检查:")
        print("     - GitHub仓库是否已创建")
        print("     - 网络连接是否正常")
        print("     - 用户名和密码/令牌是否正确")
        return False

    def check_remote_repo_exists(self) -> bool:
        """检查远程仓库是否存在"""
        print("检查远程仓库状态...")
        success, output = self.run_command(f"git ls-remote {self.remote_url}")
        return success and "HEAD" in output

    def create_github_repo_instructions(self):
        """提供GitHub仓库创建指导"""
        print("\n📋 GitHub仓库创建指南:")
        print("=" * 50)
        print("1. 访问: https://github.com/new")
        print(f"2. 仓库名称: {self.repo_name}")
        print("3. 描述: 汽车电源自动化测试框架")
        print("4. 选择Public或Private")
        print("5. 重要: 不要初始化README、.gitignore或license")
        print("6. 点击创建仓库")
        print("=" * 50)
        print("创建完成后，重新运行此脚本进行推送。")

    def run_complete_setup(self) -> bool:
        """运行完整的设置流程"""
        print("=" * 60)
        print("汽车电源测试框架 - Git仓库设置")
        print("=" * 60)
        print(f"项目路径: {self.project_path}")
        print(f"GitHub用户: {self.github_username}")
        print(f"仓库名称: {self.repo_name}")
        print("=" * 60)

        steps = [
            ("检查Git安装", self.check_git_installation),
            ("初始化仓库", self.initialize_repository),
            ("配置用户", self.configure_user_info),
            ("设置远程", self.setup_remote_repository),
            ("提交代码", self.add_and_commit_files),
        ]

        # 执行前置步骤
        for step_name, step_func in steps:
            if not step_func():
                print(f"\n❌ {step_name}失败，终止执行")
                return False
            time.sleep(0.5)

        # 检查远程仓库是否存在
        if not self.check_remote_repo_exists():
            print("\n⚠ 远程仓库不存在")
            self.create_github_repo_instructions()
            return False

        # 执行推送
        if not self.push_to_github():
            return False

        # 生成报告
        self.generate_report()
        return True

    def generate_report(self):
        """生成设置报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_path": str(self.project_path),
            "github_username": self.github_username,
            "repository": self.repo_name,
            "remote_url": self.remote_url,
            "results": self.results,
            "success": all(self.results.values())
        }

        report_file = self.project_path / "git_setup_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📊 报告已保存: {report_file.name}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 命令行参数模式
        import argparse
        parser = argparse.ArgumentParser(description="Git仓库设置工具")
        parser.add_argument("--username", required=True, help="GitHub用户名")
        parser.add_argument("--repo", default="car_power_auto_platform", help="仓库名称")
        parser.add_argument("--path", help="项目路径", default=".")
        args = parser.parse_args()

        project_path = Path(args.path).resolve()
        username = args.username
        repo_name = args.repo
    else:
        # 交互式模式
        print("汽车电源测试框架 - Git仓库设置")
        print("=" * 50)

        project_path = Path(input("项目路径 (回车使用当前目录): ").strip() or ".")
        username = input("GitHub用户名: ").strip()
        if not username:
            print("错误: 必须提供GitHub用户名")
            return 1

        repo_name = input("仓库名称 [car_power_auto_platform]: ").strip()
        if not repo_name:
            repo_name = "car_power_auto_platform"

    # 验证项目路径
    if not project_path.exists():
        print(f"错误: 路径不存在: {project_path}")
        return 1

    # 创建管理器并运行设置
    manager = GitSetupManager(project_path, username, repo_name)
    success = manager.run_complete_setup()

    if success:
        print("\n🎉 Git仓库设置完成!")
        print(f"🌐 仓库地址: https://github.com/{username}/{repo_name}")
    else:
        print("\n❌ Git仓库设置失败")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())