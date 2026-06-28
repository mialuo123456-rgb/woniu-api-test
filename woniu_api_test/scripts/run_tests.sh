#!/bin/bash
# 本地运行测试脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "========================================"
echo "  蜗牛小店 API 自动化测试"
echo "========================================"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3.x"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
pip3 install -q -r requirements.txt

# 运行测试
echo ""
echo "🚀 开始运行测试..."
echo ""

# 解析参数
MARKERS=""
VERBOSE="-v"
REPORT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--marker)
            MARKERS="-m $2"
            shift 2
            ;;
        -q|--quiet)
            VERBOSE=""
            shift
            ;;
        --report)
            REPORT="--alluredir=reports/allure-results --clean-alluredir"
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# 执行测试
pytest $VERBOSE $MARKERS $REPORT --tb=short

# 生成报告
if [[ -n "$REPORT" ]]; then
    echo ""
    echo "📊 生成 Allure 报告..."
    allure generate reports/allure-results -o reports/allure-report --clean
    echo "报告已生成: reports/allure-report/index.html"

    # 询问是否打开报告
    read -p "是否打开报告? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        allure open reports/allure-report
    fi
fi

echo ""
echo "✅ 测试完成!"
