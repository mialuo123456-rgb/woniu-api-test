#!/usr/bin/env python3
"""
API 录制脚本
使用 Playwright 监听浏览器网络请求，自动捕获 API 调用

使用方法:
    python scripts/record_api.py [--url URL] [--output FILE]

示例:
    python scripts/record_api.py --url https://webtest.woniuxiaodian.cn
    python scripts/record_api.py --output my_recording.json
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

try:
    from playwright.sync_api import sync_playwright, Page, Request, Response
except ImportError:
    print("错误: 请先安装 Playwright")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)


class APIRecorder:
    """API 请求录制器"""

    def __init__(self, base_url: str, output_file: str = None):
        self.base_url = base_url
        self.output_file = output_file or f"api_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.requests: List[Dict[str, Any]] = []
        self.api_patterns = ["/v2/", "/api/", "/service/"]  # API 路径特征

    def is_api_request(self, url: str) -> bool:
        """判断是否为 API 请求"""
        return any(pattern in url for pattern in self.api_patterns)

    def handle_request(self, request: Request):
        """处理请求"""
        if not self.is_api_request(request.url):
            return

        # 跳过静态资源
        if any(ext in request.url for ext in ['.js', '.css', '.png', '.jpg', '.ico', '.woff']):
            return

        req_data = {
            "timestamp": datetime.now().isoformat(),
            "method": request.method,
            "url": request.url,
            "path": request.url.replace(self.base_url, ""),
            "headers": dict(request.headers),
            "post_data": None,
            "response": None
        }

        # 获取请求体
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                post_data = request.post_data
                if post_data:
                    try:
                        req_data["post_data"] = json.loads(post_data)
                    except:
                        req_data["post_data"] = post_data
            except:
                pass

        self.requests.append(req_data)
        print(f"  📤 {request.method} {req_data['path']}")

    def handle_response(self, response: Response):
        """处理响应"""
        if not self.is_api_request(response.url):
            return

        # 找到对应的请求
        for req in reversed(self.requests):
            if req["url"] == response.url and req["response"] is None:
                try:
                    body = response.json()
                except:
                    body = response.text()[:500]  # 截取前500字符

                req["response"] = {
                    "status": response.status,
                    "body": body
                }

                status_icon = "✅" if response.status == 200 else "❌"
                print(f"  📥 {status_icon} {response.status}")
                break

    def start(self):
        """启动录制"""
        print("\n" + "=" * 50)
        print("  🎬 API 录制器")
        print("=" * 50)
        print(f"\n目标地址: {self.base_url}")
        print(f"输出文件: {self.output_file}")
        print("\n💡 提示:")
        print("  - 在浏览器中操作页面，API 请求会被自动捕获")
        print("  - 按 Ctrl+C 或关闭浏览器结束录制")
        print("\n" + "-" * 50)
        print("开始录制...\n")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            # 监听网络请求
            page.on("request", self.handle_request)
            page.on("response", self.handle_response)

            # 打开目标页面
            page.goto(self.base_url)

            # 等待用户操作
            try:
                while True:
                    time.sleep(1)
                    if not page.is_visible("body"):
                        break
            except KeyboardInterrupt:
                print("\n\n⏹️  录制停止")

            browser.close()

        self.save()
        self.generate_summary()

    def save(self):
        """保存录制结果"""
        output_path = Path(self.output_file)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({
                "base_url": self.base_url,
                "recorded_at": datetime.now().isoformat(),
                "total_requests": len(self.requests),
                "requests": self.requests
            }, f, ensure_ascii=False, indent=2)

        print(f"\n💾 录制已保存: {output_path}")

    def generate_summary(self):
        """生成录制摘要"""
        print("\n" + "=" * 50)
        print("  📊 录制摘要")
        print("=" * 50)
        print(f"\n总请求数: {len(self.requests)}")

        # 按方法分组
        methods = {}
        for req in self.requests:
            method = req["method"]
            methods[method] = methods.get(method, 0) + 1

        print("\n按请求方法:")
        for method, count in sorted(methods.items()):
            print(f"  {method}: {count}")

        # 列出唯一的 API 路径
        unique_paths = set()
        for req in self.requests:
            path = req["path"].split("?")[0]  # 去掉查询参数
            unique_paths.add(f"{req['method']} {path}")

        print(f"\n唯一接口 ({len(unique_paths)}):")
        for path in sorted(unique_paths):
            print(f"  • {path}")

    def generate_test_skeleton(self, output_file: str = None):
        """生成测试用例骨架"""
        output_file = output_file or "generated_tests.py"

        # 按路径分组
        api_groups = {}
        for req in self.requests:
            path = req["path"].split("?")[0]
            key = f"{req['method']}_{path.replace('/', '_').strip('_')}"
            if key not in api_groups:
                api_groups[key] = req

        # 生成测试代码
        code_lines = [
            '"""',
            '自动生成的测试用例骨架',
            f'录制时间: {datetime.now().isoformat()}',
            '"""',
            'import pytest',
            '',
            '',
            'class TestGeneratedCases:',
            '    """录制生成的测试用例"""',
            ''
        ]

        for key, req in api_groups.items():
            method = req["method"].lower()
            path = req["path"].split("?")[0]

            code_lines.append(f'    def test_{key}(self, api_client, shop_id):')
            code_lines.append(f'        """测试 {req["method"]} {path}"""')

            if req["method"] == "GET":
                code_lines.append(f'        resp = api_client.get("{path}", params={{"shop_id": shop_id}})')
            else:
                post_data = req.get("post_data", {})
                code_lines.append(f'        payload = {json.dumps(post_data, ensure_ascii=False, indent=12)}')
                code_lines.append(f'        resp = api_client.post("{path}", json=payload)')

            code_lines.append('        data = resp.json()')
            code_lines.append('        assert data["error"] == 0')
            code_lines.append('')

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(code_lines))

        print(f"\n📝 测试骨架已生成: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="API 录制脚本")
    parser.add_argument(
        "--url",
        default="https://webtest.woniuxiaodian.cn",
        help="目标网站地址"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出文件名"
    )
    parser.add_argument(
        "--generate", "-g",
        action="store_true",
        help="生成测试用例骨架"
    )

    args = parser.parse_args()

    recorder = APIRecorder(args.url, args.output)
    recorder.start()

    if args.generate:
        recorder.generate_test_skeleton()


if __name__ == "__main__":
    main()
