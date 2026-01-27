#!/usr/bin/env python3
"""
汽车电源测试框架 - Git仓库设置工具
完整版本：包含所有Git仓库设置功能
"""

import os
import sys
import subprocess
import time
import json
import argparse
from pathlib import Path
from datetime import datetime


def main():
    """主函数 - 完整的Git仓库设置工具"""
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

    # 解析路径
    project_path = Path(project_path).resolve()
    if not project_path.exists():
        print(f"❌ 错误: 项目路径不存在: {project_path}")
        return 1

    # 切换到项目目录
    os.chdir(project_path)

    print(f"\n开始设置Git仓库...")
    print(f"项目路径: {project_path}")
    print(f"GitHub用户: {username}")
    print(f"仓库名称: {repo_name}")
    print("-" * 40)

    # 定义远程URL
    remote_url = f"https://github.com/{username}/{repo_name}.git"
    web_url = f"https://github.com/{username}/{repo_name}"

    # 执行步骤
    steps = [
        ("检查Git安装", f"git --version"),
        ("初始化仓库", "git init"),
        ("配置用户", f'git config user.name "{username}"'),
        ("配置邮箱", f'git config user.email "{username}@users.noreply.github.com"'),
        ("设置远程", f"git remote add origin {remote_url}"),
        ("添加文件", "git add ."),
        ("提交更改", 'git commit -m "初始提交: 汽车电源测试框架"'),
        ("推送到GitHub", "git push -u origin main")
    ]

    # 执行所有步骤
    for i, (desc, cmd) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {desc}...")

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                print(f"   ✅ 成功")
                if result.stdout.strip():
                    output = result.stdout.strip()
                    if len(output) > 100:
                        output = output[:100] + "..."
                    print(f"      输出: {output}")
            else:
                print(f"   ❌ 失败")
                if result.stderr.strip():
                    error = result.stderr.strip()
                    if len(error) > 100:
                        error = error[:100] + "..."
                    print(f"      错误: {error}")

                # 特殊处理推送失败
                if "push" in cmd and "non-fast-forward" in result.stderr:
                    print("   🔄 检测到冲突，尝试修复...")
                    fix_commands = [
                        ("拉取远程更改", "git pull origin main --allow-unrelated-histories"),
                        ("安全推送", "git push -u origin main --force-with-lease"),
                        ("强制推送", "git push -u origin main --force")
                    ]

                    for fix_desc, fix_cmd in fix_commands:
                        print(f"      尝试: {fix_desc}...")
                        fix_result = subprocess.run(fix_cmd, shell=True, capture_output=True, text=True)
                        if fix_result.returncode == 0:
                            print(f"         ✅ 修复成功")
                            break
                        else:
                            print(f"         ❌ 修复失败")

        except Exception as e:
            print(f"   💥 异常: {e}")

    # 生成报告
    report = {
        "project": "汽车电源测试框架",
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "repository": repo_name,
        "remote_url": remote_url,
        "web_url": web_url,
        "project_path": str(project_path)
    }

    # 保存报告
    report_file = project_path / "git_setup_report.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n📄 报告已保存: {report_file}")
    except Exception as e:
        print(f"⚠️  保存报告失败: {e}")

    # 最终结果
    print("\n" + "=" * 60)
    print("设置完成!")
    print("=" * 60)
    print(f"📁 项目: {project_path}")
    print(f"🌐 仓库: {web_url}")
    print(f"👤 用户: {username}")
    print(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n后续操作:")
    print("1. 访问仓库确认: " + web_url)
    print("2. 创建新分支: git checkout -b feature/新功能")
    print("3. 提交更改: git add . && git commit -m '描述'")
    print("4. 推送分支: git push origin feature/新功能")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n程序执行异常: {e}")
        sys.exit(1)