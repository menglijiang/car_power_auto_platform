# run_tests.py
import pytest
import sys

if __name__ == "__main__":
    # 执行tests目录下的所有测试，生成Allure和HTML报告
    exit_code = pytest.main([
        "-v",
        "--tb=short",
        "--html=reports/html_report.html",
        "--alluredir=reports/allure_results",
        "tests/"
    ])
    sys.exit(exit_code)