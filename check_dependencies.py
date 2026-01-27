#!/usr/bin/env python3
"""
汽车电源测试 - 依赖检查与备份管理
功能：检查Python依赖，自动备份到backups目录
修复：解决时间戳错误，确保新备份文件时间正确
"""
import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import shutil
import time
from typing import List, Tuple, Dict


class DependencyChecker:
    """依赖检查器 - 集成备份管理"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.backup_dir = self.project_root / "backups"
        self.backup_dir.mkdir(exist_ok=True)

        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.log = logging.getLogger(__name__)

    def create_new_backup(self) -> bool:
        """
        创建新的备份文件到backups目录
        使用当前时间生成文件名，确保时间戳正确
        """
        requirements_file = self.project_root / "requirements.txt"

        if not requirements_file.exists():
            self.log.warning(f"文件不存在: {requirements_file}")
            return False

        try:
            # 使用当前时间生成时间戳
            current_time = datetime.now()
            timestamp = current_time.strftime("%Y%m%d_%H%M%S")
            backup_name = f"requirements_backup_{timestamp}.txt"
            backup_path = self.backup_dir / backup_name

            # 复制文件
            shutil.copy2(requirements_file, backup_path)

            # 设置文件创建时间为当前时间
            current_timestamp = time.mktime(current_time.timetuple())
            os.utime(backup_path, (current_timestamp, current_timestamp))

            self.log.info(f"✅ 已创建新备份: {backup_name}")
            self.log.info(f"   创建时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return True

        except Exception as e:
            self.log.error(f"❌ 创建备份失败: {e}")
            return False

    def cleanup_old_backups(self, keep_count: int = 3) -> int:
        """
        清理旧备份，保留指定数量的最新备份
        按文件名中的时间戳排序，而不是文件修改时间
        """
        try:
            # 获取所有备份文件
            backup_pattern = "requirements_backup_*.txt"
            backup_files = list(self.backup_dir.glob(backup_pattern))

            if len(backup_files) <= keep_count:
                return 0

            # 从文件名中提取时间戳并排序
            def extract_timestamp(file_path):
                # 从文件名提取时间戳：requirements_backup_YYYYMMDD_HHMMSS.txt
                name = file_path.name
                if name.startswith("requirements_backup_") and name.endswith(".txt"):
                    timestamp_str = name[20:-4]  # 移除前缀和后缀
                    try:
                        return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    except:
                        return datetime.min
                return datetime.min

            # 按文件名中的时间戳排序（最新的在前）
            backup_files.sort(key=lambda x: extract_timestamp(x), reverse=True)

            deleted_count = 0

            # 保留最新的keep_count个，删除其他的
            for i, backup_file in enumerate(backup_files):
                if i >= keep_count:
                    try:
                        backup_file.unlink()
                        deleted_count += 1
                        self.log.info(f"🗑️ 已清理旧备份: {backup_file.name}")
                    except Exception as e:
                        self.log.error(f"❌ 删除失败 {backup_file.name}: {e}")

            if deleted_count > 0:
                self.log.info(f"✅ 已清理 {deleted_count} 个旧备份文件")

            return deleted_count

        except Exception as e:
            self.log.error(f"❌ 清理备份失败: {e}")
            return 0

    def get_installed_packages(self) -> Dict[str, str]:
        """
        获取已安装的包列表
        使用 pip list 命令，返回 {包名: 版本} 字典
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=freeze"],
                capture_output=True,
                text=True,
                check=True
            )

            packages = {}
            for line in result.stdout.strip().split('\n'):
                if '==' in line:
                    pkg, ver = line.split('==', 1)
                    packages[pkg.strip().lower()] = ver.strip()

            return packages
        except subprocess.CalledProcessError as e:
            self.log.error(f"❌ 获取已安装包失败: {e}")
            return {}

    def parse_requirements(self, filepath: Path) -> List[Tuple[str, str]]:
        """
        解析requirements.txt文件
        返回(包名, 版本要求)列表
        """
        requirements = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()

                    # 跳过空行和注释
                    if not line or line.startswith('#'):
                        continue

                    # 提取包名和版本
                    if '==' in line:
                        pkg, ver = line.split('==', 1)
                        requirements.append((pkg.strip().lower(), ver.strip()))
                    else:
                        # 没有指定版本
                        requirements.append((line.strip().lower(), ''))

        except Exception as e:
            self.log.error(f"❌ 解析requirements.txt失败: {e}")

        return requirements

    def check_dependencies(self) -> Tuple[List[str], List[str]]:
        """
        检查缺失的依赖
        返回(缺失的依赖列表, 已满足的依赖列表)
        """
        requirements_file = self.project_root / "requirements.txt"

        if not requirements_file.exists():
            self.log.error("❌ requirements.txt文件不存在")
            return [], []

        # 创建新备份
        backup_created = self.create_new_backup()
        if not backup_created:
            self.log.warning("⚠ 备份创建失败，继续检查依赖")

        # 清理旧备份
        self.cleanup_old_backups(3)

        # 获取已安装的包
        installed = self.get_installed_packages()

        # 解析requirements.txt
        required = self.parse_requirements(requirements_file)

        missing = []
        satisfied = []

        for pkg, required_ver in required:
            if pkg in installed:
                installed_ver = installed[pkg]

                if required_ver and installed_ver != required_ver:
                    missing.append(f"{pkg}=={required_ver} (已安装: {installed_ver})")
                else:
                    satisfied.append(f"{pkg}=={installed_ver}" if installed_ver else pkg)
            else:
                missing.append(f"{pkg}=={required_ver}" if required_ver else pkg)

        return missing, satisfied

    def show_backup_status(self):
        """显示备份文件状态"""
        try:
            backup_files = list(self.backup_dir.glob("requirements_backup_*.txt"))

            if backup_files:
                # 从文件名中提取时间戳并排序
                def extract_timestamp(file_path):
                    name = file_path.name
                    if name.startswith("requirements_backup_") and name.endswith(".txt"):
                        timestamp_str = name[20:-4]
                        try:
                            return datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        except:
                            return datetime.min
                    return datetime.min

                backup_files.sort(key=lambda x: extract_timestamp(x), reverse=True)

                print(f"\n📁 备份文件状态 (共 {len(backup_files)} 个):")
                print("-" * 60)
                for i, file_path in enumerate(backup_files, 1):
                    # 从文件名中提取创建时间
                    timestamp = extract_timestamp(file_path)
                    if timestamp != datetime.min:
                        time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        time_str = "未知时间"

                    file_size = file_path.stat().st_size
                    status = "🟢 最新" if i == 1 else "🟡 保留" if i <= 3 else "🔴 待清理"
                    print(f"  {status} {i:2d}. {file_path.name}")
                    print(f"      创建: {time_str}")
                    print(f"      大小: {file_size:,} bytes")
                    if i == 3:
                        print("-" * 60)
            else:
                print("\n📁 当前没有备份文件")

        except Exception as e:
            print(f"\n⚠ 无法显示备份状态: {e}")

    def install_missing_dependencies(self, missing: List[str]) -> bool:
        """
        安装缺失的依赖
        返回是否全部安装成功
        """
        if not missing:
            return True

        self.log.info(f"🔧 开始安装 {len(missing)} 个缺失的依赖")

        all_success = True
        for dep in missing:
            try:
                # 提取包名（去掉版本信息）
                pkg = dep.split('==')[0] if '==' in dep else dep

                self.log.info(f"📦 正在安装: {pkg}")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", pkg],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    self.log.info(f"✅ 安装成功: {pkg}")
                else:
                    self.log.error(f"❌ 安装失败 {pkg}: {result.stderr[:200]}")
                    all_success = False

            except Exception as e:
                self.log.error(f"❌ 安装 {dep} 时出错: {e}")
                all_success = False

        return all_success

    def run(self) -> bool:
        """
        运行完整的依赖检查流程
        返回是否所有依赖都已满足
        """
        print("=" * 60)
        print("🚗 汽车电源测试框架 - 依赖检查工具")
        print("📁 备份文件保存至: backups/")
        print("=" * 60)

        # 检查缺失依赖
        missing, satisfied = self.check_dependencies()

        # 显示备份状态
        self.show_backup_status()

        # 显示依赖检查结果
        if satisfied:
            print(f"\n✅ 已满足的依赖 ({len(satisfied)} 个):")
            for dep in satisfied:  # 显示全部依赖，不再截断
                print(f"  ✓ {dep}")

        if missing:
            print(f"\n❌ 缺失的依赖 ({len(missing)} 个):")
            for dep in missing:
                print(f"  ✗ {dep}")

            # 询问是否安装
            print("\n" + "=" * 60)
            response = input("是否自动安装缺失的依赖? (y/n): ")
            if response.lower() == 'y':
                success = self.install_missing_dependencies(missing)
                if success:
                    print("\n🎉 所有依赖安装完成！")
                else:
                    print("\n⚠ 部分依赖安装失败，请手动安装")
                return success
            else:
                return False
        else:
            print("\n🎉 所有依赖均已满足！")
            return True


def main():
    """主函数"""
    try:
        checker = DependencyChecker()
        success = checker.run()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⏹️ 操作被用户中断")
        return 130
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())