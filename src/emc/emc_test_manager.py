# src/emc/emc_test_manager.py
class EMCTestManager:
    """EMC测试管理 - 文档2.5.2节要求"""

    def conduct_dpi_test(self, frequency_ranges: list):
        """直接射频功率注入测试 - 文档2.5.2.3"""
        for freq_range in frequency_ranges:
            start, end, step = freq_range
            freq = start
            while freq <= end:
                self._inject_rf_power(freq, power_dbm=30)  # 全局Pin 30dBm
                self._monitor_functional_status()
                freq += step

    def test_conducted_emission(self):
        """传导发射测试 - 150Ω法, 0.1-1000MHz"""
        frequencies = self._generate_test_frequencies(0.1, 1000)
        results = {}
        for freq in frequencies:
            emission = self._measure_emission(freq)
            results[freq] = emission
            self._check_compliance(freq, emission)  # 验证是否符合限值