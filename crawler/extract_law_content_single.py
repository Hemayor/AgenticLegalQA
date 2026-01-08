# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import re
import time
import os

def extract_law_content(url):
    print(f"🔍 正在抓取: {url}")


    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url)
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    # -----------------------------
    # 基本信息
    # -----------------------------
    #提取标题
    title_tag = soup.find("h2", class_="title")
    title = title_tag.find(text=True, recursive=False).strip() if title_tag else ""

    #提取法宝引证码
    law_code_tag = soup.find("a", string=re.compile(r"CLI\."))
    law_code = law_code_tag.get_text(strip=True) if law_code_tag else ""

    #提取制定机关
    promulgating_authority_tag = soup.find("a", attrs={"logfunc": "制定机关"})
    promulgating_authority = promulgating_authority_tag.get_text(strip=True) if promulgating_authority_tag else ""

    #提取公布日期、施行日期
    def get_date(label):
        tag = soup.find("strong", string=re.compile(label))
        if tag:
            return tag.parent.get_text(strip=True).replace(label, "").replace(".", "-")
        return ""

    published_date = get_date("公布日期：")
    effective_date = get_date("施行日期：")

    #提取效力位阶
    legal_level_tag = soup.find("a", attrs={"logfunc": "效力位阶"})
    legal_level = legal_level_tag.get_text(strip=True) if legal_level_tag else ""

    #提取法规类别
    category_tags = soup.select("div.box span a[logfunc='法规类别']")
    category = [t.get_text(strip=True) for t in category_tags]

    # -----------------------------
    # 章节 + 条文
    # -----------------------------
    chapters = []
    for chap in soup.select("p.navzhang"):
        chapter_title = chap.get_text(strip=True).replace("　", " ")
        chapter = {"chapter_title": chapter_title, "articles": []}

        for sib in chap.find_all_next():
            if sib.name == "p" and "navzhang" in sib.get("class", []):
                break

            if sib.name == "div" and "tiao-wrap" in sib.get("class", []):
                tiao_tag = sib.select_one("span.navtiao")
                article_number = tiao_tag.get_text(strip=True) if tiao_tag else ""

                kuan_contents = sib.select("div.kuan-content")

                content = "\n".join(
                    kc.get_text(strip=True).replace(article_number, "").strip()
                    for kc in kuan_contents
                )

                # 司法案例
                judicial_tag = sib.select_one("a[href^='/clink/pfnl']")
                judicial_case = ""
                if judicial_tag:
                    judicial_case = "https://www.pkulaw.com" + judicial_tag["href"]

                # 提取 relevant_laws（只来自正文 alink）
                relevant_laws = []
                for kc in kuan_contents:
                    for a in kc.select("a.alink"):
                        name = a.get_text(strip=True)
                        if name not in relevant_laws:
                            relevant_laws.append(name)

                chapter["articles"].append({
                    "article_number": article_number,
                    "content": content,
                    "judicial_case": judicial_case,
                    "relevant_laws": relevant_laws
                })

        chapters.append(chapter)

    return {
        "title": title,
        "law_code": law_code,
        "promulgating_authority": promulgating_authority,
        "published_date": published_date,
        "effective_date": effective_date,
        "legal_level": legal_level,
        "category": category,
        "chapters": chapters
    }

# ======================================================
# 批量处理入口
# ======================================================
def extract_from_txt(txt_path, output_json):
    all_laws = []

    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    urls = []
    for line in lines:
        match = re.search(r"https?://\S+", line)
        if match:
            urls.append(match.group())

    print(f"📄 共发现 {len(urls)} 个法律链接")

    for idx, url in enumerate(urls, 1):
        print(f"\n➡️ ({idx}/{len(urls)}) 开始处理")
        try:
            law_data = extract_law_content(url)
            all_laws.append(law_data)
        except Exception as e:
            print(f"❌ 失败: {url}")
            print(e)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_laws, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 全部完成，已保存为 {output_json}")

# -----------------------------
# 主入口
# -----------------------------
if __name__ == "__main__":
    extract_from_txt(
        txt_path="test.txt",
        output_json="pkulaw_legal.json"
    )
