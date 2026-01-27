#!/usr/bin/env python3
"""
汽车电源测试框架 - Git仓库设置工具（智能版）
修复远程仓库检测逻辑，避免重复创建
版本: v4.1.0
"""
import os
import sys
import subprocess
import time
import json
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict


class GitSetupTool:
    """Git仓库设置工具 - 智能版本"""

    def __init__(self, username: str, repo_name: str, project_path: Path,
                 use_ssh: bool = False, verbose: bool = False):
        self.username = username
        self.repo_name = repo_name
        self.project_path = project_path
        self.use_ssh = use_ssh
        self.verbose = verbose

        if use_ssh:
            self.remote_url = f"git@github.com:{username}/{repo_name}.git"
        else:
            self.remote_url = f"https://github.com/{username}/{repo_name}.git"

        self.repo_web_url = f"https://github.com/{username}/{repo_name}"
        self.results = {}
        self.start_time = datetime.now()

        if not self._validate_project_path():
            sys.exit(1)

        os.chdir(self.project_path)

    def _validate_project_path(self) -> bool:
        """验证项目路径"""
        if not self.project_path.exists():
            print(f"❌ 错误: 项目路径不存在: {self.project_path}")
            return False

        if not self.project_path.is_dir():
            print(f"❌ 错误: 项目路径不是目录: {self.project_path}")
            return False

        return True

    def _print_header(self, title: str):
        """打印标题"""
        print(f"\n{'=' * 60}")
        print(f"{title.center(60)}")
        print(f"{'=' * 60}")

    def _print_step(self, step_num: int, total_steps: int, description: str):
        """打印步骤信息"""
        print(f"\n[{step_num}/{total_steps}] {description}")

    def _print_status(self, message: str, status: str = "info"):
        """打印状态消息"""
        symbols = {"success": "✅", "error": "❌", "warning": "⚠️", "info": "ℹ️"}
        print(f"  {symbols.get(status, '')} {message}")

    def _run_command(self, cmd: str, description: str = "", show_output: bool = False) -> Tuple[bool, str]:
        """运行命令并返回结果"""
        try:
            if self.verbose and description:
                print(f"    执行: {cmd}")

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
                self.results[description] = {
                    "success": success,
                    "command": cmd,
                    "output": output[:500] if len(output) > 500 else output,
                    "timestamp": datetime.now().isoformat()
                }

            if show_output and output and not success:
                lines = output.split('\n')
                for line in lines[:3]:
                    if line.strip():
                        print(f"        {line}")
                if len(lines) > 3:
                    print(f"        ... 还有 {len(lines) - 3} 行输出")

            return success, output

        except subprocess.TimeoutExpired:
            self._print_status("命令执行超时", "error")
            return False, "命令执行超时"
        except Exception as e:
            self._print_status(f"执行异常: {e}", "error")
            return False, str(e)

    def check_remote_repository_exists(self) -> bool:
        """检查远程仓库是否存在"""
        self._print_status("检查GitHub仓库状态")

        # 方法1: 检查远程仓库URL是否可访问
        check_success, check_output = self._run_command(
            f"git ls-remote {self.remote_url} HEAD",
            "检查远程仓库可访问性"
        )

        if check_success:
            self._print_status("远程仓库存在且可访问", "success")
            return True

        # 方法2: 检查GitHub网页是否存在（通过HTTP状态码）
        try:
            import urllib.request
            request = urllib.request.Request(
                self.repo_web_url,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                if response.status == 200:
                    self._print_status("GitHub仓库页面存在", "success")
                    return True
        except:
            pass

        self._print_status("远程仓库不存在或无法访问", "warning")
        return False

    def setup_remote_repository(self) -> bool:
        """智能设置远程仓库"""
        self._print_step(4, 7, "配置远程仓库")

        # 首先检查远程仓库是否已配置
        remote_check_success, remote_output = self._run_command("git remote -v", "检查当前远程配置")

        if remote_check_success and "origin" in remote_output:
            self._print_status("远程仓库已配置", "info")

            # 获取当前配置的URL
            url_success, current_url = self._run_command("git remote get-url origin", "获取当前远程URL")
            if url_success:
                self._print_status(f"当前URL: {current_url}", "info")

                if current_url == self.remote_url:
                    self._print_status("远程配置正确，无需修改", "success")
                    return True
                else:
                    self._print_status("URL不匹配，需要更新", "warning")
                    # 更新远程URL
                    update_success, _ = self._run_command(
                        f"git remote set-url origin {self.remote_url}",
                        "更新远程仓库URL"
                    )
                    if update_success:
                        self._print_status("远程URL更新成功", "success")
                        return True
                    else:
                        self._print_status("更新失败，尝试重新添加", "error")
                        # 删除后重新添加
                        self._run_command("git remote remove origin", "删除旧配置")

        # 检查远程仓库是否存在
        if not self.check_remote_repository_exists():
            self._print_status("请先在GitHub创建仓库", "warning")
            self._print_status(f"创建地址: https://github.com/new", "info")
            return False

        # 添加新的远程仓库
        add_success, _ = self._run_command(
            f"git remote add origin {self.remote_url}",
            "添加远程仓库"
        )

        if add_success:
            self._print_status("远程仓库配置成功", "success")
            return True
        else:
            self._print_status("远程仓库配置失败", "error")
            return False

    def check_requirements(self) -> bool:
        """检查系统要求"""
        self._print_step(1, 7, "检查系统要求")
        git_success, git_output = self._run_command("git --version", "检查Git安装")

        if not git_success:
            self._print_status("Git未安装或不可用", "error")
            return False

        version = git_output.split()[-1] if git_output else "未知版本"
        self._print_status(f"Git版本: {version}", "success")
        self._print_status(f"项目目录: {self.project_path}", "success")
        return True

    def setup_git_config(self) -> bool:
        """设置Git配置"""
        self._print_step(2, 7, "配置Git用户信息")
        name_success, _ = self._run_command(f'git config user.name "{self.username}"', "设置用户名")
        email = f"{self.username}@users.noreply.github.com"
        email_success, _ = self._run_command(f'git config user.email "{email}"', "设置邮箱")

        if name_success and email_success:
            self._print_status(f"用户: {self.username} <{email}>", "success")
            return True
        else:
            self._print_status("用户配置失败", "error")
            return False

    def initialize_git_repo(self) -> bool:
        """初始化Git仓库"""
        self._print_step(3, 7, "初始化Git仓库")
        git_dir = self.project_path / ".git"
        if git_dir.exists():
            self._print_status("Git仓库已存在", "info")
            branch_success, branch_output = self._run_command("git branch --show-current", "检查当前分支")
            if branch_success and branch_output:
                self._print_status(f"当前分支: {branch_output}", "info")
            return True

        init_success, _ = self._run_command("git init", "初始化仓库")
        if init_success:
            self._print_status("Git仓库初始化成功", "success")
            return True
        else:
            self._print_status("Git仓库初始化失败", "error")
            return False

    def commit_changes(self) -> bool:
        """提交更改"""
        self._print_step(5, 7, "提交代码更改")
        status_success, status_output = self._run_command("git status --porcelain", "检查Git状态")

        if not status_success:
            self._print_status("检查Git状态失败", "error")
            return False

        files = [line for line in status_output.split('\n') if line.strip()]
        if not files:
            self._print_status("没有需要提交的更改", "info")
            return True

        self._print_status(f"检测到 {len(files)} 个文件", "info")
        add_success, _ = self._run_command("git add .", "添加文件")

        if not add_success:
            self._print_status("添加文件失败", "error")
            return False

        commit_message = f"""初始提交: 汽车电源自动化测试框架

项目: {self.repo_name}
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
描述: 48V电源模块自动化测试平台
"""

        commit_success, _ = self._run_command(f'git commit -m "{commit_message}"', "提交更改")
        if commit_success:
            self._print_status(f"提交成功 ({len(files)}个文件)", "success")
            return True
        else:
            self._print_status("提交失败", "error")
            return False

    def fix_non_fast_forward(self) -> bool:
        """修复non-fast-forward冲突"""
        self._print_status("检测到non-fast-forward冲突，尝试修复...", "warning")

        # 尝试拉取并合并
        pull_success, _ = self._run_command(
            "git pull origin main --allow-unrelated-histories",
            "拉取远程更改"
        )

        if pull_success:
            self._run_command('git commit -m "自动合并: 解决冲突"', "提交合并")

        # 安全强制推送
        force_success, _ = self._run_command(
            "git push -u origin main --force-with-lease",
            "安全强制推送",
            show_output=True
        )
        if force_success:
            self._print_status("安全强制推送成功", "success")
            return True

        # 最终强制推送
        final_success, _ = self._run_command(
            "git push -u origin main --force",
            "最终强制推送",
            show_output=True
        )
        if final_success:
            self._print_status("强制推送成功", "success")
            return True

        return False

    def push_to_github(self, max_retries: int = 3) -> bool:
        """推送到GitHub"""
        self._print_step(6, 7, "推送到GitHub")

        # 检查远程仓库是否存在
        if not self.check_remote_repository_exists():
            self._print_status("远程仓库不存在，请先创建", "error")
            return False

        for attempt in range(max_retries):
            if attempt > 0:
                self._print_status(f"重试推送 ({attempt}/{max_retries})", "warning")
                time.sleep(2)

            push_success, push_output = self._run_command(
                "git push -u origin main",
                "推送到GitHub",
                show_output=True
            )

            if push_success:
                self._print_status("代码推送成功", "success")
                return True
            else:
                if "non-fast-forward" in push_output:
                    if self.fix_non_fast_forward():
                        return True
                elif "failed to push" in push_output:
                    self._print_status("推送被拒绝", "warning")

        self._print_status("推送失败", "error")
        return False

    def verify_setup(self) -> bool:
        """验证设置结果"""
        self._print_step(7, 7, "验证设置结果")
        status_success, _ = self._run_command("git status", "检查本地状态")
        if status_success:
            self._print_status("本地仓库状态正常", "success")

        remote_success, _ = self._run_command("git remote -v", "检查远程连接")
        if remote_success:
            self._print_status("远程连接正常", "success")

        return True

    def run(self) -> bool:
        """运行完整的设置流程"""
        self._print_header("汽车电源测试框架 - Git仓库设置工具")
        print(f"\n配置信息:")
        print(f"  项目路径: {self.project_path}")
        print(f"  GitHub用户: {self.username}")
        print(f"  仓库名称: {self.repo_name}")
        print(f"  远程仓库: {self.repo_web_url}")

        steps = [
            ("检查系统要求", self.check_requirements),
            ("配置Git用户", self.setup_git_config),
            ("初始化Git仓库", self.initialize_git_repo),
            ("设置远程仓库", self.setup_remote_repository),  # 使用新的智能方法
            ("提交代码更改", self.commit_changes),
            ("推送到GitHub", self.push_to_github),
            ("验证设置结果", self.verify_setup),
        ]

        all_success = True

        for step_name, step_func in steps:
            try:
                if not step_func():
                    all_success = False
                    if step_name in ["检查系统要求", "配置Git用户", "初始化Git仓库"]:
                        self._print_status("关键步骤失败，终止执行", "error")
                        break
            except Exception as e:
                self._print_status(f"步骤执行异常: {str(e)}", "error")
                all_success = False
                break

        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "project": "汽车电源测试框架",
            "username": self.username,
            "repository": self.repo_name,
            "remote_url": self.remote_url,
            "web_url": self.repo_web_url,
            "results": self.results,
            "success": all_success
        }

        # 保存报告
        report_file = self.project_path / "git_setup_report.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self._print_status(f"报告已保存: {report_file.name}", "info")
        except Exception as e:
            self._print_status(f"保存报告失败: {e}", "warning")

        # 最终结果
        self._print_header("设置完成")
        if all_success:
            print(f"✅ Git仓库设置已完成!")
            print(f"🌐 仓库地址: {self.repo_web_url}")
        else:
            print(f"⚠️ Git仓库设置未完全完成")

        return all_success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="汽车电源测试框架 - Git仓库设置工具")
    parser.add_argument("--username", help="GitHub用户名")
    parser.add_argument("--repo", help="仓库名称")
    parser.add_argument("--path", help="项目路径", default=".")
    parser.add_argument("--ssh", action="store_true", help="使用SSH协议")
    parser.add_argument("--verbose", action="store_true", help="详细模式")
    args = parser.parse_args()

    # 获取输入
    username = args.username or input("GitHub用户名: ").strip()
    if not username:
        print("❌ 必须提供GitHub用户名")
        return 1

    repo_name = args.repo or input("仓库名称: ").strip()
    if not repo_name:
        print("❌ 必须提供仓库名称")
        return 1

    project_path = Path(args.path or input("项目路径: ").strip() or ".")
    project_path = project_path.resolve()

    try:
        tool = GitSetupTool(username, repo_name, project_path, args.ssh, args.verbose)
        success = tool.run()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        return 130
    except Exception as e:
        print(f"\n程序执行异常: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())