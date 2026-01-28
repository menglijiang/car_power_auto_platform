#!/usr/bin/env python3
"""
汽车电源测试框架 - Git仓库设置工具（增强版）
专为 menglijiang/car_power_auto_platform 仓库优化
版本: v8.0.0 - 修复用户名验证，支持多种配置方式
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
from typing import Tuple, Dict, Optional


class Colors:
    """控制台颜色定义"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'


def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.RESET}")


def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.RESET}")


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.RESET}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.RESET}")


def print_step(step_num: int, total_steps: int, description: str):
    print(f"\n{Colors.CYAN}[步骤 {step_num}/{total_steps}] {description}{Colors.RESET}")


def run_command(cmd: str, cwd: str = None, show_output: bool = False) -> Tuple[bool, str]:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=30
        )
        success = result.returncode == 0
        output = result.stdout.strip() or result.stderr.strip()

        if show_output and output and not success:
            for line in output.split('\n')[:3]:
                if line.strip():
                    print(f"    {line}")

        return success, output
    except Exception as e:
        return False, str(e)


def detect_git_config():
    """检测现有的Git配置"""
    config = {}
    success, name = run_command("git config --global user.name")
    if success and name:
        config["username"] = name.strip()
    return config


def validate_github_username(username: str) -> Tuple[bool, str]:
    """验证GitHub用户名 - 修复版"""
    if not username or not username.strip():
        return False, "GitHub用户名不能为空"

    username = username.strip()

    # 更宽松的验证：允许数字用户名，但检查基本格式
    if len(username) > 39:
        return False, "GitHub用户名过长（最多39字符）"

    # GitHub实际允许纯数字用户名（如用户ID），但建议使用字母数字组合
    pattern = r'^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$'
    if not re.match(pattern, username):
        return False, "用户名包含无效字符（只能包含字母、数字和连字符）"

    return True, ""


def get_github_username():
    """获取GitHub用户名，提供清晰指引"""
    # 检测现有配置
    git_config = detect_git_config()
    if "username" in git_config:
        current_user = git_config["username"]
        print(f"检测到Git配置用户: {current_user}")

        # 验证当前用户
        valid, msg = validate_github_username(current_user)
        if valid:
            use_current = input(f"使用当前用户 '{current_user}'? (Y/n): ").strip().lower()
            if use_current in ['', 'y', 'yes']:
                return current_user

    while True:
        username = input("GitHub用户名: ").strip()
        if not username:
            print_error("用户名不能为空")
            continue

        valid, msg = validate_github_username(username)
        if valid:
            return username
        else:
            print_error(f"用户名无效: {msg}")
            print_info("提示: 使用您在GitHub.com上显示的用户名")


def check_remote_repo_exists(remote_url: str) -> bool:
    """检查远程仓库是否存在"""
    success, _ = run_command(f"git ls-remote {remote_url} HEAD", timeout=10)
    return success


def smart_setup_remote(project_path: str, remote_url: str, repo_name: str, username: str) -> bool:
    """智能设置远程仓库"""
    print_info("检查远程配置...")

    # 检查是否已配置
    check_success, check_output = run_command("git remote -v", project_path)

    if check_success and "origin" in check_output:
        print_info("远程仓库已配置")

        # 获取当前URL
        url_success, current_url = run_command("git remote get-url origin", project_path)
        if url_success:
            print_info(f"当前URL: {current_url}")

            if current_url.strip() == remote_url:
                print_success("远程配置正确")
                return True
            else:
                print_warning("远程URL不匹配")
                # 更新URL
                update_success, _ = run_command(f"git remote set-url origin {remote_url}", project_path)
                if update_success:
                    print_success("远程URL更新成功")
                    return True

    # 检查远程仓库是否存在
    if not check_remote_repo_exists(remote_url):
        print_warning("远程仓库可能不存在")
        print_info(f"请确认仓库存在: https://github.com/{username}/{repo_name}")
        create = input("是否继续? (y/N): ").lower()
        if create not in ['y', 'yes']:
            return False

    # 添加远程仓库
    add_success, output = run_command(f"git remote add origin {remote_url}", project_path)

    if add_success or "already exists" in output:
        print_success("远程仓库配置成功")
        return True

    print_error("远程仓库配置失败")
    return False


def check_git_status(project_path: str) -> Tuple[bool, int]:
    """检查Git状态，返回是否有更改和文件数量"""
    success, output = run_command("git status --porcelain", project_path)
    if not success:
        return False, 0

    files = [line for line in output.split('\n') if line.strip()]
    return True, len(files)


def get_commit_message() -> str:
    """获取提交信息"""
    default_msg = "汽车电源测试框架代码更新"
    print(f"提交理由 (回车使用默认): {default_msg}")
    user_msg = input("您的理由: ").strip()

    if not user_msg:
        user_msg = default_msg

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"{user_msg} - {timestamp}"


def handle_push_conflict(project_path: str) -> bool:
    """处理推送冲突"""
    print_warning("检测到推送冲突")

    # 先尝试拉取
    print_info("尝试拉取远程更改...")
    pull_success, _ = run_command("git pull origin main --allow-unrelated-histories", project_path, True)

    if pull_success:
        # 提交合并
        run_command('git commit -m "合并远程更改"', project_path)

    # 安全强制推送
    print_info("尝试安全强制推送...")
    force_success, _ = run_command("git push -u origin main --force-with-lease", project_path, True)
    if force_success:
        return True

    # 最终强制推送（需要确认）
    confirm = input("是否尝试强制推送? (y/N): ").lower()
    if confirm in ['y', 'yes']:
        final_success, _ = run_command("git push -u origin main --force", project_path, True)
        return final_success

    return False


def main():
    print("=" * 60)
    print("汽车电源测试框架 - Git仓库设置工具")
    print("=" * 60)

    # 获取配置信息
    print("\n配置信息:")
    print("-" * 40)

    # GitHub用户名
    username = get_github_username()

    # 仓库名称
    repo_name = input("仓库名称 [car_power_auto_platform]: ").strip()
    if not repo_name:
        repo_name = "car_power_auto_platform"

    # 项目路径
    project_path = input("项目路径: ").strip()
    if not project_path:
        project_path = "."

    project_path = Path(project_path).resolve()
    if not project_path.exists():
        print_error(f"项目路径不存在: {project_path}")
        return 1

    # 协议选择
    use_ssh = input("使用SSH协议? (y/N): ").strip().lower() in ['y', 'yes']
    if use_ssh:
        remote_url = f"git@github.com:{username}/{repo_name}.git"
        print_info("使用SSH协议")
    else:
        remote_url = f"https://github.com/{username}/{repo_name}.git"
        print_info("使用HTTPS协议")

    repo_web_url = f"https://github.com/{username}/{repo_name}"

    print(f"\n开始设置...")
    print(f"项目路径: {project_path}")
    print(f"GitHub用户: {username}")
    print(f"仓库名称: {repo_name}")
    print(f"远程仓库: {repo_web_url}")
    print("-" * 50)

    # 执行步骤
    steps = [
        ("检查Git安装", "git --version"),
        ("初始化仓库", "git init"),
        ("配置用户", f'git config user.name "{username}"'),
        ("配置邮箱", f'git config user.email "{username}@users.noreply.github.com"'),
        ("智能远程设置", ""),  # 特殊处理
        ("检查代码状态", ""),  # 特殊处理
        ("添加文件", "git add ."),
        ("提交更改", ""),  # 特殊处理
        ("推送到GitHub", "git push -u origin main"),
    ]

    all_success = True
    has_changes = True

    for i, (desc, cmd) in enumerate(steps, 1):
        print_step(i, len(steps), desc)

        if desc == "智能远程设置":
            success = smart_setup_remote(str(project_path), remote_url, repo_name, username)
        elif desc == "检查代码状态":
            status_ok, file_count = check_git_status(str(project_path))
            if status_ok:
                if file_count == 0:
                    print_warning("没有检测到更改")
                    has_changes = False
                    # 跳过后续步骤
                    steps[i] = ("添加文件", "skip")
                    steps[i + 1] = ("提交更改", "skip")
                    steps[i + 2] = ("推送到GitHub", "skip")
                    success = True
                else:
                    print_success(f"检测到 {file_count} 个文件需要提交")
                    success = True
            else:
                success = False
        elif desc == "提交更改":
            if not has_changes:
                print_info("跳过提交（无更改）")
                success = True
            else:
                commit_msg = get_commit_message()
                success, output = run_command(f'git commit -m "{commit_msg}"', str(project_path))
        elif cmd == "skip":
            print_info("跳过步骤")
            success = True
        else:
            success, output = run_command(cmd, str(project_path))

        if success:
            print_success("完成")
        else:
            print_error("失败")

            # 特殊错误处理
            if "non-fast-forward" in output and "推送到GitHub" in desc:
                if handle_push_conflict(str(project_path)):
                    success = True
                    print_success("冲突解决成功")

            if not success:
                all_success = False
                if desc in ["检查Git安装", "初始化仓库"]:
                    break

    # 生成报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "repository": repo_name,
        "remote_url": remote_url,
        "web_url": repo_web_url,
        "project_path": str(project_path),
        "success": all_success
    }

    # 保存报告
    report_file = project_path / "git_setup_report.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print_info(f"报告已保存: {report_file.name}")
    except Exception as e:
        print_warning(f"保存报告失败: {e}")

    # 最终结果
    print("\n" + "=" * 60)
    if all_success:
        print_success("Git仓库设置完成!")
        if has_changes:
            print(f"代码已推送到: {repo_web_url}")
        else:
            print("本地仓库已配置，但无新更改可提交")
    else:
        print_error("设置未完全成功")

    return 0 if all_success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"程序执行异常: {e}")
        sys.exit(1)