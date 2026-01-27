# src/production/test_coverage.py
class ProductionTestCoverage:
    """生产测试覆盖率 - 文档2.8节100%覆盖率要求"""

    def calculate_coverage(self) -> dict:
        """计算测试覆盖率"""
        coverage = {
            'aoi_axi': self._get_aoi_coverage(),  # 自动光学检测
            'ict': self._get_ict_coverage(),  # 在线测试
            'eol': self._get_eol_coverage(),  # 端到端测试
            'burn_in': self._get_burn_in_coverage()  # 老化测试
        }

        total = sum(coverage.values()) / len(coverage)
        assert total >= 1.0, f"测试覆盖率不足100%: {total * 100:.1f}%"
        return coverage

    def run_aging_test(self, hours: int, temperature: float):
        """老化测试 - SOP+6以内4小时，之后2小时"""
        start_time = time.time()
        while time.time() - start_time < hours * 3600:
            self._cycle_power()  # 空载/带载循环
            self._monitor_parameters()
            if self._detect_failure():
                self._log_failure()