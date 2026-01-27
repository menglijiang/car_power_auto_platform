#!/usr/bin/env python3
"""
备份文件管理脚本
功能：清理项目根目录中的备份文件，确保新备份保存到backups目录
"""
import os
import sys
from pathlib import Path
import glob
from datetime import datetime


class BackupManager:
    """备份文件管理类"""

    def __init__(self):
        """初始化备份管理器"""
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)  # 确保backups目录存在

    def clean_existing_backups(self):
        """清理现有备份文件"""
        print("=" * 50)
        print("开始清理备份文件")
        print("=" * 50)

        deleted_files = []

        # 清理项目根目录中的备份文件
        patterns = [
            "requirements_backup_*.txt",
            "requirements.txt.bak",
            "requirements.txt.backup",
            "*.backup",
            "*.bak"
        ]

        for pattern in patterns:
            for file_path in self.project_root.glob(pattern):
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path.name)
                    print(f"✓ 已删除: {file_path.name}")
                except Exception as e:
                    print(f"✗ 删除失败 {file_path.name}: {e}")

        # 清理backups目录，只保留最新的3个备份
        if self.backup_dir.exists():
            backup_files = list(self.backup_dir.glob("requirements_backup_*.txt"))
            if backup_files:
                # 按修改时间排序（最新的在前面）
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

                # 保留最新的3个，删除其他的
                if len(backup_files) > 3:
                    for old_file in backup_files[3:]:
                        try:
                            os.remove(old_file)
                            deleted_files.append(f"backups/{old_file.name}")
                            print(f"✓ 已删除旧备份: backups/{old_file.name}")
                        except Exception as e:
                            print(f"✗ 删除失败 {old_file.name}: {e}")

        return deleted_files

    def show_status(self):
        """显示备份文件状态"""
        print("\n" + "=" * 50)
        print("当前备份文件状态")
        print("=" * 50)

        # 检查项目根目录
        root_backups = []
        for pattern in ["requirements_backup_*.txt", "*.bak", "*.backup"]:
            root_backups.extend(list(self.project_root.glob(pattern)))

        if root_backups:
            print(f"项目根目录中发现 {len(root_backups)} 个备份文件:")
            for file_path in root_backups:
                print(f"  📄 {file_path.name}")
        else:
            print("✓ 项目根目录中没有备份文件")

        # 检查backups目录
        if self.backup_dir.exists():
            backup_files = list(self.backup_dir.glob("requirements_backup_*.txt"))
            if backup_files:
                print(f"\nbackups目录中有 {len(backup_files)} 个备份文件:")
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                for i, file_path in enumerate(backup_files[:3], 1):
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    print(f"  {i}. {file_path.name}")
                    print(f"     创建时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print("\nbackups目录中没有备份文件")

    def setup_backup_system(self):
        """设置备份系统"""
        print("\n" + "=" * 50)
        print("设置备份系统")
        print("=" * 50)

        # 确保backups目录存在
        self.backup_dir.mkdir(exist_ok=True)
        print(f"✓ 确保backups目录存在: {self.backup_dir}")

        print("\n✅ 备份系统设置完成")
        print("   所有新备份文件将自动保存到: backups/")


def main():
    """主函数"""
    print("备份文件管理工具")
    print("=" * 50)

    # 创建管理器实例
    manager = BackupManager()

    # 显示当前状态
    manager.show_status()

    # 询问是否清理现有备份
    response = input("\n是否清理所有现有备份文件? (y/n): ")
    if response.lower() == 'y':
        deleted = manager.clean_existing_backups()
        if deleted:
            print(f"\n✅ 清理完成，共删除 {len(deleted)} 个文件")
        else:
            print("\n✅ 没有需要清理的文件")

    # 设置备份系统
    manager.setup_backup_system()

    # 显示最终状态
    manager.show_status()

    print("\n" + "=" * 50)
    print("使用说明:")
    print("1. 后续所有备份将自动保存到 backups/ 目录")
    print("2. 系统自动保留最新的3个备份文件")
    print("=" * 50)

    return True


if __name__ == "__main__":
    try:
        if main():
            print("\n🎉 备份管理系统设置完成！")
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
    except Exception as e:
        print(f"\n错误: {e}")