#!/usr/bin/env python3
"""
汽车电源测试框架 - Git仓库设置工具（增强版）
支持用户输入和智能仓库检测
版本: v4.3.0
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
    # 使用git ls-remote检查仓库可访问性
    check_success, check_output = run_command(f"git ls-remote {remote_url} HEAD")
    return check_success


def smart_setup_remote(project_path, remote_url):
    """智能设置远程仓库 - 先检查后操作"""
    print("   🔍 检查当前远程配置...")

    # 检查是否已配置远程仓库
    check_success, check_output = run_command("git remote -v", project_path)

    if check_success and "origin" in check_output:
        print("   ✅ 远程仓库已配置")

        # 获取当前URL
        url_success, current_url = run_command("git remote get-url origin", project_path)
        if url_success:
            print(f"   当前URL: {current_url}")

            if current_url == remote_url:
                print("   ✅ 远程配置正确，无需修改")
                return True
            else:
                print("   🔄 更新远程URL...")
                # 更新远程URL
                update_success, _ = run_command(f"git remote set-url origin {remote_url}", project_path)
                if update_success:
                    print("   ✅ 远程URL更新成功")
                    return True
                else:
                    print("   ❌ 更新失败，尝试重新添加")
                    # 删除后重新添加
                    run_command("git remote remove origin", project_path)

    # 检查远程仓库是否存在
    if not check_remote_repo_exists(remote_url):
        print("   ⚠️ 远程仓库不存在或无法访问")
        return False

    # 添加新的远程仓库
    add_success, _ = run_command(f"git remote add origin {remote_url}", project_path)
    if add_success:
        print("   ✅ 远程仓库配置成功")
        return True

    return False


def main():
    print("=" * 60)
    print("汽车电源测试框架 - Git仓库设置工具")
    print("=" * 60)

    # 获取用户输入（保持现有逻辑不变）
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
        print("❌ 错误: 必须提供项目路径")
        return 1

    # 验证项目路径
    project_path = Path(project_path).resolve()
    if not project_path.exists():
        print(f"❌ 错误: 项目路径不存在: {project_path}")
        return 1

    if not project_path.is_dir():
        print(f"❌ 错误: 项目路径不是目录: {project_path}")
        return 1

    # 构建远程URL
    remote_url = f"https://github.com/{username}/{repo_name}.git"
    repo_web_url = f"https://github.com/{username}/{repo_name}"

    print(f"\n开始设置Git仓库...")
    print(f"项目路径: {project_path}")
    print(f"GitHub用户: {username}")
    print(f"仓库名称: {repo_name}")
    print(f"远程URL: {remote_url}")
    print("-" * 50)

    # 切换到项目目录
    os.chdir(project_path)

    # 修复步骤（保持现有逻辑，只增强远程仓库设置）
    steps = [
        ("检查Git安装", "git --version"),
        ("初始化仓库", "git init"),
        ("配置用户信息", f'git config user.name "{username}"'),
        ("配置用户邮箱", f'git config user.email "{username}@users.noreply.github.com"'),
        ("智能设置远程仓库", ""),  # 特殊处理
        ("添加所有文件", "git add ."),
        ("提交更改", 'git commit -m "汽车电源测试框架完整提交"'),
        ("推送到GitHub", "git push -u origin main")
    ]

    all_success = True
    results = {}

    for i, (desc, cmd) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {desc}...")

        # 特殊处理远程仓库配置
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

            # 特殊错误处理（保持现有逻辑）
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
            # 最终尝试标准强制推送
            print("      🔥 尝试最终强制推送...")
            final_success, _ = run_command("git push -u origin main --force", project_path)
            if final_success:
                success = True
                print("      ✅ 最终强制推送成功")

        if not success:
            all_success = False

    # 生成报告（保持现有逻辑）
    report = {
        "timestamp": datetime.now().isoformat(),
        "project": "汽车电源测试框架",
        "username": username,
        "repository": repo_name,
        "remote_url": remote_url,
        "web_url": repo_web_url,
        "project_path": str(project_path),
        "success": all_success,
        "results": results
    }

    # 保存报告
    report_file = project_path / "git_setup_report.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 报告已保存: {report_file}")
    except Exception as e:
        print(f"⚠️ 保存报告失败: {e}")

    # 最终结果
    print("\n" + "=" * 60)
    if all_success:
        print("🎉 Git仓库设置完成!")
    else:
        print("⚠️ 设置未完全成功")

    print(f"\n项目信息:")
    print(f"  项目路径: {project_path}")
    print(f"  远程仓库: {repo_web_url}")
    print(f"  GitHub用户: {username}")

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