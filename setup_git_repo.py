#!/usr/bin/env python3
"""
汽车电源测试框架 - Git仓库自动化设置脚本（修复版）
修复提交失败问题，自动配置Git用户信息
"""
import os
import sys
import subprocess
import time
from pathlib import Path
import getpass


class GitRepositorySetup:
    """Git仓库自动化设置类（修复版）"""

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
                return result
            else:
                print(f"  ✗ 失败: {result.stderr[:200] if result.stderr else '无错误信息'}")
                return result

        except Exception as e:
            print(f"  ✗ 异常: {e}")
            return None

    def check_git_installed(self):
        """检查Git是否已安装"""
        return self.run_command("git --version", "检查Git安装")

    def initialize_git_repo(self):
        """初始化Git仓库"""
        git_dir = self.project_path / ".git"
        if git_dir.exists():
            print("ℹ️  Git仓库已存在，跳过初始化")
            return True

        result = self.run_command("git init", "初始化Git仓库")
        return result.returncode == 0 if result else False

    def configure_git_user(self):
        """配置Git用户信息（修复提交失败的关键步骤）"""
        print("🔧 配置Git用户信息...")

        # 获取系统用户名
        system_user = getpass.getuser()

        # 如果提供了GitHub用户名，使用它
        if self.github_username:
            user_name = self.github_username
        else:
            user_name = system_user

        # 设置用户名
        name_result = self.run_command(f'git config user.name "{user_name}"', "设置用户名")

        # 设置邮箱（使用GitHub的noreply邮箱格式）
        if self.github_username:
            email = f"{self.github_username}@users.noreply.github.com"
        else:
            email = f"{system_user}@localhost"

        email_result = self.run_command(f'git config user.email "{email}"', "设置邮箱")

        # 验证配置
        self.run_command("git config --list | grep user", "验证用户配置")

        return (name_result.returncode == 0 if name_result else False) and \
            (email_result.returncode == 0 if email_result else False)

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

        # 如果.gitignore已存在，备份
        if gitignore_path.exists():
            backup_path = self.project_path / ".gitignore.backup"
            with open(gitignore_path, 'r', encoding='utf-8') as src:
                with open(backup_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            print("ℹ️  .gitignore已存在，已创建备份")

        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print("✓  创建/更新.gitignore文件")

        return True

    def create_required_dirs(self):
        """创建必要的空目录"""
        required_dirs = ['backups', 'logs', 'reports']

        for dir_name in required_dirs:
            dir_path = self.project_path / dir_name
            dir_path.mkdir(exist_ok=True)

            if dir_name == 'reports':
                gitkeep = dir_path / '.gitkeep'
                gitkeep.touch(exist_ok=True)

        print("✓  创建必要的目录结构")
        return True

    def get_files_to_add(self):
        """获取需要添加的文件列表"""
        result = self.run_command("git status --porcelain", "检查文件状态")
        if not result or result.returncode != 0:
            return []

        files = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # 提取文件名（移除状态标记）
                file_status = line[:2]
                filename = line[3:]
                files.append((file_status.strip(), filename))

        return files

    def add_and_commit_files(self):
        """添加并提交所有文件（修复版）"""
        print("🔧 添加并提交文件...")

        # 检查是否有文件可添加
        files = self.get_files_to_add()
        if not files:
            print("ℹ️  没有检测到需要添加的文件")
            return True

        print(f"ℹ️  检测到 {len(files)} 个文件需要处理")

        # 添加所有文件
        add_result = self.run_command("git add .", "添加所有文件到暂存区")
        if not add_result or add_result.returncode != 0:
            return False

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

        if commit_result and commit_result.returncode == 0:
            return True
        else:
            # 如果提交失败，尝试查看原因
            self.run_command("git status", "查看Git状态")
            return False

    def rename_main_branch(self):
        """重命名主分支为main"""
        # 检查当前分支
        branch_result = self.run_command("git branch", "检查当前分支")
        if branch_result and "master" in branch_result.stdout:
            result = self.run_command("git branch -M main", "重命名主分支为main")
            return result.returncode == 0 if result else False
        else:
            print("ℹ️  当前分支不是master，跳过重命名")
            return True

    def add_remote_origin(self):
        """添加远程仓库"""
        if not self.github_username:
            print("⚠️  未提供GitHub用户名，跳过远程仓库设置")
            return False

        # 检查是否已设置远程仓库
        remote_result = self.run_command("git remote -v", "检查远程仓库")
        if remote_result and "origin" in remote_result.stdout:
            print("ℹ️  远程仓库已存在，跳过添加")
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
                if line.strip():
                    print(f"    {line}")
            return True
        return False

    def push_to_remote(self):
        """推送到远程仓库"""
        print("🔧 推送到远程仓库...")

        # 检查远程仓库是否存在
        remote_check = self.run_command("git ls-remote origin", "检查远程仓库访问")
        if remote_check and remote_check.returncode != 0:
            print("⚠️  远程仓库不存在或无法访问")
            print(f"   请在GitHub创建仓库: {self.repo_name}")
            print(f"   仓库URL: {self.remote_url}")
            return False

        result = self.run_command("git push -u origin main", "推送到远程仓库")

        if result and result.returncode == 0:
            print(f"🎉 代码推送成功!")
            print(f"🌐 您的仓库地址: https://github.com/{self.github_username}/{self.repo_name}")
            return True
        else:
            print("⚠️  推送失败，可能需要手动创建远程仓库")
            print(f"   请在GitHub创建仓库: {self.repo_name}")
            print(f"   然后运行: git push -u origin main")
            return False

    def get_git_status(self):
        """获取Git状态"""
        result = self.run_command("git status", "获取Git状态")
        if result and result.returncode == 0:
            print("\n📊 当前Git状态:")
            print(result.stdout)

    def show_commit_history(self):
        """显示提交历史"""
        result = self.run_command("git log --oneline -5", "显示最近5次提交")
        if result and result.returncode == 0:
            print("\n📜 提交历史:")
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
        print("汽车电源测试框架 - Git仓库自动化设置（修复版）")
        print("=" * 60)

        steps = [
            ("检查Git安装", self.check_git_installed),
            ("初始化Git仓库", self.initialize_git_repo),
            ("配置Git用户信息", self.configure_git_user),
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
                print("\n💡 建议: 请检查Git配置，确保已正确设置用户名和邮箱")
                print("   您可以通过以下命令手动设置:")
                print("   git config --global user.name '您的姓名'")
                print("   git config --global user.email '您的邮箱'")
                return False
            time.sleep(0.5)

        self.get_git_status()
        self.show_commit_history()
        self.setup_complete()
        return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Git仓库自动化设置（修复版）")
    parser.add_argument("--path", help="项目路径，默认为当前目录")
    parser.add_argument("--username", help="GitHub用户名")
    parser.add_argument("--repo", help="仓库名称", default="car_power_auto_platform")

    args = parser.parse_args()

    if not args.username:
        print("❌ 错误: 必须提供GitHub用户名")
        print("   使用 --username 参数指定GitHub用户名")
        sys.exit(1)

    setup = GitRepositorySetup(
        project_path=args.path,
        github_username=args.username,
        repo_name=args.repo
    )

    success = setup.run_full_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        print("Git仓库自动化设置（修复版）")
        print("=" * 60)

        project_path = input("项目路径 (回车使用当前目录): ").strip() or None
        github_username = input("GitHub用户名: ").strip()

        if not github_username:
            print("❌ 必须提供GitHub用户名")
            sys.exit(1)

        repo_name = input("仓库名称 (回车使用默认): ").strip() or "car_power_auto_platform"

        setup = GitRepositorySetup(
            project_path=project_path,
            github_username=github_username,
            repo_name=repo_name
        )

        success = setup.run_full_setup()
        sys.exit(0 if success else 1)
