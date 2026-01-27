#!/usr/bin/env python3
"""
汽车电源测试框架 - 修复版Git仓库设置工具
解决编码问题和远程配置冲突
版本: v4.0.0
"""
import os
import sys
import subprocess
import time
import json
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
            encoding='utf-8',  # 强制使用UTF-8编码
            errors='replace',
            timeout=30
        )
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("汽车电源测试框架 - Git仓库修复工具")
    print("=" * 60)

    # 配置信息
    username = "menglijiang"
    repo_name = "car_power_auto_platform"
    project_path = Path("D:/Pycharm/Projects/xiangshan")
    remote_url = f"https://github.com/{username}/{repo_name}.git"

    print(f"项目路径: {project_path}")
    print(f"GitHub用户: {username}")
    print(f"仓库名称: {repo_name}")
    print(f"远程URL: {remote_url}")
    print()

    # 修复步骤
    steps = [
        ("检查当前状态", "git status"),
        ("检查远程配置", "git remote -v"),
        ("修复远程仓库", f"git remote set-url origin {remote_url}"),
        ("配置用户信息", f'git config user.name "{username}"'),
        ("配置用户邮箱", f'git config user.email "{username}@users.noreply.github.com"'),
        ("添加所有文件", "git add ."),
        ("提交更改", 'git commit -m "汽车电源测试框架完整提交"'),
        ("强制推送到GitHub", "git push -u origin main --force")
    ]

    all_success = True

    for i, (desc, cmd) in enumerate(steps, 1):
        print(f"[{i}/{len(steps)}] {desc}...")

        # 特殊处理远程仓库配置
        if "修复远程仓库" in desc:
            # 先检查是否已配置
            check_success, check_output = run_command("git remote -v", project_path)
            if check_success and "origin" in check_output:
                # 已存在，使用set-url更新
                success, output = run_command(cmd, project_path)
            else:
                # 不存在，添加新的
                add_cmd = f"git remote add origin {remote_url}"
                success, output = run_command(add_cmd, project_path)
        else:
            success, output = run_command(cmd, project_path)

        if success:
            print("   ✅ 成功")
            if output and len(output) < 100:
                print(f"      输出: {output}")
        else:
            print("   ❌ 失败")
            if output:
                error_msg = output[:200] + "..." if len(output) > 200 else output
                print(f"      错误: {error_msg}")

            # 特殊错误处理
            if "already exists" in output:
                print("      ℹ️ 远程已存在，继续执行")
                success = True  # 视为成功继续
            elif "non-fast-forward" in output:
                print("      🔄 检测到冲突，尝试安全强制推送...")
                force_success, _ = run_command("git push -u origin main --force-with-lease", project_path)
                if force_success:
                    success = True
                    print("      ✅ 安全强制推送成功")

        if not success and desc in ["强制推送到GitHub"]:
            # 最终尝试标准强制推送
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
        "web_url": f"https://github.com/{username}/{repo_name}",
        "project_path": str(project_path),
        "success": all_success
    }

    # 保存报告
    report_file = project_path / "git_fix_report.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 修复报告已保存: {report_file}")
    except Exception as e:
        print(f"⚠️ 保存报告失败: {e}")

    # 最终结果
    print("\n" + "=" * 60)
    if all_success:
        print("🎉 Git仓库修复完成!")
        print(f"🌐 仓库地址: https://github.com/{username}/{repo_name}")
    else:
        print("⚠️ 修复未完全成功，请检查上述错误")

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