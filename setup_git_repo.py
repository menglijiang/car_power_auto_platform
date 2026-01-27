#!/usr/bin/env python3
"""
汽车电源测试框架 - 修复版Git仓库设置工具
简化版本，解决编码和远程仓库问题
"""
import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',  # 强制使用UTF-8编码
            errors='ignore'
        )
        return result.returncode == 0, result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return False, str(e)


def main():
    print("汽车电源测试框架 - Git仓库修复工具")
    print("=" * 50)

    # 项目信息
    project_path = Path("D:/Pycharm/Projects/xiangshan")
    username = "menglijiang"
    repo_name = "car_power_auto_platform"
    remote_url = f"https://github.com/{username}/{repo_name}.git"

    print(f"项目路径: {project_path}")
    print(f"远程仓库: {remote_url}")
    print()

    # 修复步骤
    steps = [
        ("检查Git状态", "git status"),
        ("配置用户信息", f'git config user.name "{username}"'),
        ("配置邮箱", f'git config user.email "{username}@users.noreply.github.com"'),
        ("检查远程仓库", "git remote -v"),
        ("重新设置远程仓库", f"git remote set-url origin {remote_url}"),
        ("添加文件", "git add ."),
        ("提交更改", 'git commit -m "修复提交: 汽车电源测试框架"'),
        ("推送到GitHub", "git push -u origin main --force-with-lease")
    ]

    for i, (desc, cmd) in enumerate(steps, 1):
        print(f"{i}. {desc}...")
        success, output = run_command(cmd, project_path)

        if success:
            print(f"   ✅ 成功")
            if output and len(output) < 100:  # 只显示简短输出
                print(f"     输出: {output}")
        else:
            print(f"   ❌ 失败")
            if "already exists" in output:
                print(f"      已存在，跳过")
                continue
            elif "fatal:" in output:
                print(f"      错误: {output}")

    print("\n" + "=" * 50)
    print("修复完成！")
    print(f"仓库地址: https://github.com/{username}/{repo_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())