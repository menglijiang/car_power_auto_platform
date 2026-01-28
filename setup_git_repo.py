#!/usr/bin/env python3
"""
汽车电源测试框架 - Git仓库设置工具（增强版）
支持自定义提交理由和智能仓库检测
版本: v4.4.0
"""
import os
import sys
import subprocess
import time
import json
import argparse
from pathlib import Path
from datetime import datetime


def run_command(cmd, cwd=None):
    """运行命令并处理编码问题"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=30
        )
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return False, str(e)


def check_remote_repo_exists(remote_url):
    """检查远程仓库是否存在"""
    print("   🔍 检查远程仓库状态...")
    check_success, check_output = run_command(f"git ls-remote {remote_url} HEAD")
    return check_success


def smart_setup_remote(project_path, remote_url):
    """智能设置远程仓库 - 先检查后操作"""
    print("   🔍 检查当前远程配置...")

    check_success, check_output = run_command("git remote -v", project_path)

    if check_success and "origin" in check_output:
        print("   ✅ 远程仓库已配置")

        url_success, current_url = run_command("git remote get-url origin", project_path)
        if url_success:
            print(f"   当前URL: {current_url}")

            if current_url == remote_url:
                print("   ✅ 远程配置正确，无需修改")
                return True
            else:
                print("   🔄 更新远程URL...")
                update_success, _ = run_command(f"git remote set-url origin {remote_url}", project_path)
                if update_success:
                    print("   ✅ 远程URL更新成功")
                    return True
                else:
                    print("   ❌ 更新失败，尝试重新添加")
                    run_command("git remote remove origin", project_path)

    if not check_remote_repo_exists(remote_url):
        print("   ⚠️ 远程仓库不存在或无法访问")
        return False

    add_success, _ = run_command(f"git remote add origin {remote_url}", project_path)
    if add_success:
        print("   ✅ 远程仓库配置成功")
        return True

    return False


def get_commit_message(default_reason="汽车电源测试框架代码提交"):
    """获取用户自定义的提交理由"""
    print("\n📝 请输入提交理由（按回车使用默认理由）:")
    print(f"   默认理由: {default_reason}")
    user_reason = input("   您的提交理由: ").strip()

    if not user_reason:
        user_reason = default_reason
        print("   ✅ 使用默认提交理由")
    else:
        print("   ✅ 使用自定义提交理由")

    # 构建完整的提交消息
    commit_message = f"""{user_reason}

项目: 汽车电源测试框架
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
描述: 48V电源模块自动化测试平台
"""
    return commit_message


def main():
    print("=" * 60)
    print("汽车电源测试框架 - Git仓库设置工具")
    print("=" * 60)

    # 获取用户输入
    print("\n请输入配置信息:")
    print("-" * 40)

    username = input("GitHub用户名: ").strip()
    if not username:
        print("❌ 错误: 必须提供GitHub用户名")
        return 1

    repo_name = input("仓库名称: ").strip()
    if not repo_name:
        print("❌ 错误: 必须提供仓库名称")
        return 1

    project_path = input("项目路径: ").strip()
    if not project_path:
        project_path = "."

    project_path = Path(project_path).resolve()
    if not project_path.exists():
        print(f"❌ 错误: 项目路径不存在: {project_path}")
        return 1

    os.chdir(project_path)

    remote_url = f"https://github.com/{username}/{repo_name}.git"
    repo_web_url = f"https://github.com/{username}/{repo_name}"

    print(f"\n开始设置Git仓库...")
    print(f"项目路径: {project_path}")
    print(f"GitHub用户: {username}")
    print(f"仓库名称: {repo_name}")
    print("-" * 50)

    # 获取提交理由
    commit_message = get_commit_message()

    # 定义执行步骤
    steps = [
        ("检查Git安装", "git --version"),
        ("初始化仓库", "git init"),
        ("配置用户", f'git config user.name "{username}"'),
        ("配置邮箱", f'git config user.email "{username}@users.noreply.github.com"'),
        ("智能设置远程仓库", ""),  # 特殊处理
        ("添加文件", "git add ."),
        ("提交更改", f'git commit -m "{commit_message}"'),  # 使用自定义消息
        ("推送到GitHub", "git push -u origin main")
    ]

    results = {}
    all_success = True

    for i, (desc, cmd) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {desc}...")

        if "智能设置远程仓库" in desc:
            success = smart_setup_remote(project_path, remote_url)
            output = "智能远程仓库配置"
        else:
            success, output = run_command(cmd, project_path)

        results[desc] = success

        if success:
            print("   ✅ 成功")
            if output and len(output) < 100 and output != "智能远程仓库配置":
                print(f"      输出: {output}")
        else:
            print("   ❌ 失败")
            if output:
                error_msg = output[:200] + "..." if len(output) > 200 else output
                print(f"      错误: {error_msg}")

            if "already exists" in output:
                print("      ℹ️ 已存在，继续执行")
                success = True
            elif "non-fast-forward" in output and "push" in cmd:
                print("      🔄 检测到冲突，尝试安全强制推送...")
                force_success, _ = run_command("git push -u origin main --force-with-lease", project_path)
                if force_success:
                    success = True
                    print("      ✅ 安全强制推送成功")

        if not success and desc in ["推送到GitHub"]:
            print("      🔥 尝试最终强制推送...")
            final_success, _ = run_command("git push -u origin main --force", project_path)
            if final_success:
                success = True
                print("      ✅ 最终强制推送成功")

        if not success:
            all_success = False

    # 生成报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "project": "汽车电源测试框架",
        "username": username,
        "repository": repo_name,
        "remote_url": remote_url,
        "web_url": repo_web_url,
        "project_path": str(project_path),
        "commit_message": commit_message,  # 记录提交理由
        "success": all_success,
        "results": results
    }

    report_file = project_path / "git_setup_report.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 报告已保存: {report_file}")
    except Exception as e:
        print(f"⚠️ 保存报告失败: {e}")

    print("\n" + "=" * 60)
    if all_success:
        print("🎉 Git仓库设置完成!")
    else:
        print("⚠️ 设置未完全完成")

    print(f"\n项目信息:")
    print(f"  提交理由: {commit_message.splitlines()[0]}")  # 显示提交理由
    print(f"  项目路径: {project_path}")
    print(f"  远程仓库: {repo_web_url}")

    return 0 if all_success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n程序执行异常: {e}")
        sys.exit(1)