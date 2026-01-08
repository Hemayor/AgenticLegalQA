# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright, TimeoutError
import time

# 存放抓取到的 URL
all_urls = []

# def wait_for_slider_and_manual(page):
#     """
#     检测滑块验证码，如果出现就等待人工处理
#     """
#     try:
#         page.wait_for_selector(
#             "iframe[src*='geetest'], .geetest_slider_button",
#             timeout=5000
#         )
#         print("\n⚠️ 检测到滑块验证码")
#         print("👉 请在浏览器中【手动拖动滑块】")
#         input("✔️ 完成后按【回车】继续程序...\n")
#         time.sleep(2)  # 滑块完成后的等待
#     except TimeoutError:
#         # 没有滑块，正常继续
#         pass

with sync_playwright() as p:
    # 1. 启动浏览器
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    # 2. 打开北大法宝首页
    page.goto("https://www.pkulaw.com/")
    page.wait_for_load_state("networkidle")

    # 3. 点击“司法解释➕” → “司法解释”
    page.wait_for_selector("#EffectivenessDicport_18_switch", timeout=60000)
    page.locator("#EffectivenessDicport_18_switch").click()
    time.sleep(1)

    page.wait_for_selector("#EffectivenessDicport_19_span", timeout=60000)
    page.locator("#EffectivenessDicport_19_span").click()
    time.sleep(1)

    # 4. 点击“现行有效”
    page.wait_for_selector("#TimelinessDicport_1_span", timeout=60000)
    page.locator("#TimelinessDicport_1_span").click()
    time.sleep(1)

    # 检测滑块
    # wait_for_slider_and_manual(page)

    # 5. hover 20 条/页 → 下拉 → 点击 100 条/页
    page.wait_for_selector(".articleSelect > div:first-child", timeout=60000)
    page.locator(".articleSelect > div:first-child").hover()
    time.sleep(1)

    page.wait_for_selector("dd[filter_value='100']:visible", timeout=60000)
    page.locator("dd[filter_value='100']:visible").click()
    time.sleep(2)

    # 检测滑块
    # wait_for_slider_and_manual(page)

    # 6. 循环抓取，每页手动翻页，最多8页
    page_index = 1
    while page_index <= 7:
        print(f"\n📄 正在抓取第 {page_index} 页")

        # 等待文章列表加载
        page.wait_for_selector("a[flink='true']", timeout=60000)
        links = page.locator("a[flink='true']")
        count = links.count()
        for i in range(count):
            title = links.nth(i).inner_text().strip()
            href = links.nth(i).get_attribute("href")
            if not href:
                continue
            # 只保留法规总页，不抓 Readchl
            if "/chl/" in href and "listView" in href:
                # 跳过包含“决定”或“决议”的法规
                if "决定" in title or "决议" in title:
                    continue
                full_url = page.url.split("?")[0].rstrip("/") + href
                all_urls.append((title, full_url))
                print(f"{len(all_urls)}. {title} {full_url}")

        print("\n✅ 当前页抓取完成")
        if page_index < 7:
            input("👉 请手动点击下一页后按【回车】继续抓取下一页...\n")
            # wait_for_slider_and_manual(page)
        page_index += 1

    # 7. 输出总数
    print(f"\n共抓取 {len(all_urls)} 条法规 URL")

    # 8. 关闭浏览器
    browser.close()

# 9. 保存到文件，带序号
with open("pkulaw_judicialExplanation_urls.txt", "w", encoding="utf-8") as f:
    for idx, (title, url) in enumerate(all_urls, 1):
        f.write(f"{idx}. {title}\t{url}\n")

print("完成，已保存 pkulaw_judicialExplanation_urls.txt")
