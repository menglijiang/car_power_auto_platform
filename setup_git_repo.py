#!/usr/bin/env python3
"""
汽车电源测试框架 - Git仓库自动化设置脚本
解决特殊字符问题，提供完整的Git配置流程
"""
import os
import sys
import subprocess
import time
from pathlib import Path
import json


class GitRepositorySetup:
    """Git仓库自动化设置类"""

    def __init__(self, project_path=None, github_username=None, repo_name="car_power_auto_platform"):
        """
        初始化Git仓库设置

        Args:
            project_path: 项目路径，默认为当前目录
            github_username: GitHub用户名
            repo_name: 仓库名称
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.github_username = github_username
        self.repo_name = repo_name
        self.remote_url = f"https://github.com/{github_username}/{repo_name}.git"

        # 确保在项目目录中
        os.chdir(self.project_path)

    def run_command(self, command, description=""):
        """运行命令并返回结果"""
        print(f"🔧 {description}...")

        try:
            # 使用subprocess运行命令，避免终端特殊字符问题
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            if result.returncode == 0:
                print(f"  ✓ 成功")
                if result.stdout.strip():
                    print(f"    输出: {result.stdout.strip()[:100]}")
            else:
                print(f"  ✗ 失败: {result.stderr[:200]}")

            return result
        except Exception as e:
            print(f"  ✗ 异常: {e}")
            return None

    def check_git_installed(self):
        """检查Git是否已安装"""
        return self.run_command("git --version", "检查Git安装")

    def initialize_git_repo(self):
        """初始化Git仓库"""
        # 检查是否已经是Git仓库
        git_dir = self.project_path / ".git"
        if git_dir.exists():
            print("ℹ️  Git仓库已存在")
            return True

        result = self.run_command("git init", "初始化Git仓库")
        return result.returncode == 0 if result else False

    def create_gitignore(self):
        """创建.gitignore文件"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
backups/*.txt
logs/*.log
reports/**/*
!reports/.gitkeep

# Test reports
htmlcov/
.coverage
.coverage.*
.pytest_cache/
.mypy_cache/

# Configurations
*.local.yaml
*.secret.yaml

# Data files
*.csv
*.xlsx
*.db
*.sqlite3

# Jupyter Notebook
.ipynb_checkpoints

# Documentation
docs/_build/

# Temporary files
*.tmp
*.temp
"""

        gitignore_path = self.project_path / ".gitignore"
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("✓  创建.gitignore文件")

        return True

    def create_required_dirs(self):
        """创建必要的空目录"""
        required_dirs = ['backups', 'logs', 'reports']

        for dir_name in required_dirs:
            dir_path = self.project_path / dir_name
            dir_path.mkdir(exist_ok=True)

            # 在reports目录中添加.gitkeep文件
            if dir_name == 'reports':
                gitkeep = dir_path / '.gitkeep'
                gitkeep.touch(exist_ok=True)

        print("✓  创建必要的目录结构")
        return True

    def add_and_commit_files(self):
        """添加并提交所有文件"""
        # 添加所有文件
        add_result = self.run_command("git add .", "添加所有文件到暂存区")
        if not add_result or add_result.returncode != 0:
            return False

        # 获取文件数量
        status_result = self.run_command("git status --porcelain", "检查文件状态")
        if status_result and status_result.stdout:
            file_count = len([line for line in status_result.stdout.split('\n') if line.strip()])
            print(f"  ℹ️  检测到 {file_count} 个文件")

        # 提交文件
        commit_message = """初始提交: 汽车电源自动化测试框架

- 电源管理模块
- 安全监控系统
- 测试配置文件
- 依赖检查脚本
- 完整的测试用例
- 符合SOR文档V1.0技术要求
"""

        commit_cmd = f'git commit -m "{commit_message}"'
        commit_result = self.run_command(commit_cmd, "提交初始版本")
        return commit_result.returncode == 0 if commit_result else False

    def rename_main_branch(self):
        """重命名主分支为main"""
        result = self.run_command("git branch -M main", "重命名主分支为main")
        return result.returncode == 0 if result else False

    def add_remote_origin(self):
        """添加远程仓库"""
        if not self.github_username:
            print("⚠️  未提供GitHub用户名，跳过远程仓库设置")
            return False

        # 检查是否已设置远程仓库
        remote_result = self.run_command("git remote -v", "检查远程仓库")
        if remote_result and "origin" in remote_result.stdout:
            print("ℹ️  远程仓库已存在")
            return True

        # 添加远程仓库
        add_cmd = f'git remote add origin {self.remote_url}'
        result = self.run_command(add_cmd, "添加远程仓库")
        return result.returncode == 0 if result else False

    def verify_remote_connection(self):
        """验证远程连接"""
        result = self.run_command("git remote -v", "验证远程连接")
        if result and result.returncode == 0:
            print("✓  远程仓库配置:")
            for line in result.stdout.strip().split('\n'):
                print(f"    {line}")
            return True
        return False

    def push_to_remote(self):
        """推送到远程仓库"""
        result = self.run_command("git push -u origin main", "推送到远程仓库")

        if result and result.returncode == 0:
            print(f"🎉 代码推送成功!")
            print(f"🌐 您的仓库地址: https://github.com/{self.github_username}/{self.repo_name}")
            return True
        else:
            print("⚠️  推送失败，可能需要先创建远程仓库")
            print(f"   请在GitHub创建仓库: {self.repo_name}")
            return False

    def get_git_status(self):
        """获取Git状态"""
        result = self.run_command("git status", "获取Git状态")
        if result and result.returncode == 0:
            print("\n📊 当前Git状态:")
            print(result.stdout)

    def setup_complete(self):
        """完成设置"""
        print("\n" + "=" * 60)
        print("Git仓库设置完成!")
        print("=" * 60)

        if self.github_username:
            print(f"\n📁 本地仓库: {self.project_path}")
            print(f"🌐 远程仓库: https://github.com/{self.github_username}/{self.repo_name}")

        print("\n📋 后续操作指南:")
        print("1. 创建新分支: git checkout -b feature/新功能名称")
        print("2. 提交更改: git add . && git commit -m '描述'")
        print("3. 推送分支: git push origin feature/新功能名称")
        print("4. 在GitHub创建Pull Request")
        print("5. 查看仓库: https://github.com/YOUR_USERNAME/car_power_auto_platform")
        print("\n" + "=" * 60)

    def run_full_setup(self):
        """运行完整的设置流程"""
        print("=" * 60)
        print("汽车电源测试框架 - Git仓库自动化设置")
        print("=" * 60)

        steps = [
            ("检查Git安装", self.check_git_installed),
            ("初始化Git仓库", self.initialize_git_repo),
            ("创建.gitignore文件", self.create_gitignore),
            ("创建必要目录", self.create_required_dirs),
            ("添加并提交文件", self.add_and_commit_files),
            ("重命名主分支", self.rename_main_branch),
        ]

        if self.github_username:
            steps.extend([
                ("添加远程仓库", self.add_remote_origin),
                ("验证远程连接", self.verify_remote_connection),
                ("推送到远程仓库", self.push_to_remote),
            ])

        for step_name, step_func in steps:
            print(f"\n[{steps.index((step_name, step_func)) + 1}/{len(steps)}] ", end="")
            if not step_func():
                print(f"\n❌ 步骤 '{step_name}' 失败，停止执行")
                return False
            time.sleep(0.5)  # 短暂延迟，提高可读性

        self.get_git_status()
        self.setup_complete()
        return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Git仓库自动化设置")
    parser.add_argument("--path", help="项目路径，默认为当前目录")
    parser.add_argument("--username", help="GitHub用户名", required=True)
    parser.add_argument("--repo", help="仓库名称", default="car_power_auto_platform")

    args = parser.parse_args()

    # 创建设置器实例
    setup = GitRepositorySetup(
        project_path=args.path,
        github_username=args.username,
        repo_name=args.repo
    )

    # 运行完整设置
    success = setup.run_full_setup()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    # 如果没有提供命令行参数，使用交互式方式
    if len(sys.argv) > 1:
        main()
    else:
        print("Git仓库自动化设置")
        print("=" * 60)

        # 交互式输入
        project_path = input("项目路径 (回车使用当前目录): ").strip() or None
        github_username = input("GitHub用户名: ").strip()
        repo_name = input("仓库名称 (回车使用默认): ").strip() or "car_power_auto_platform"

        setup = GitRepositorySetup(
            project_path=project_path,
            github_username=github_username,
            repo_name=repo_name
        )

        success = setup.run_full_setup()
        sys.exit(0 if success else 1)
