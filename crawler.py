import sys
from typing import Dict, List, Optional, Tuple, Union

import requests
from bs4 import BeautifulSoup


BAIDU_SEARCH_URL = "https://www.baidu.com/s"

def build_headers() -> Dict[str, str]:
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

def fetch(query: str, extra_params: Optional[Dict[str, str]] = None, timeout: int = 20) -> requests.Response:
    params = {"wd": query}
    if extra_params:
        params.update(extra_params)
    headers = build_headers()
    resp = requests.get(BAIDU_SEARCH_URL, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp

def parse_results(html: str, limit: Optional[int] = None) -> List[Tuple[str, str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    containers = soup.select("#content_left .c-container, #content_left .result")
    results: List[Tuple[str, str, str]] = []
    for c in containers:
        t_el = c.select_one("h3 a") or c.select_one("h3")
        title = t_el.get_text(strip=True) if t_el else ""
        url = t_el.get("href", "") if t_el else ""
        if not title:
            title = c.get_text(strip=True)[:100]
        texts = []
        for s in c.stripped_strings:
            if s and s != title:
                texts.append(s)
        snippet = " ".join(texts)
        if len(snippet) > 400:
            snippet = snippet[:400]
        results.append((title, url, snippet))
        if limit is not None and len(results) >= limit:
            break
    if results:
        return results
    plain = soup.get_text("\n", strip=True)
    if limit is not None:
        plain = plain[:2000]
    return [("", "", plain)]

def to_text(results: List[Tuple[str, str, str]]) -> str:
    lines: List[str] = []
    for idx, (title, url, snippet) in enumerate(results, 1):
        if title:
            lines.append(f"[{idx}] {title}")
        else:
            lines.append(f"[{idx}]")
        if url:
            lines.append(url)
        if snippet:
            lines.append(snippet)
        lines.append("")
    return "\n".join(lines).strip()

def to_html(query: str, results: List[Tuple[str, str, str]]) -> str:
    html_lines: List[str] = [
        "<!DOCTYPE html>",
        "<html lang=\"zh-CN\">",
        "<head>",
        "    <meta charset=\"UTF-8\">",
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
        f"    <title>百度搜索结果: {query}</title>",
        "    <style>",
        "        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }",
        "        .container { max-width: 800px; margin: auto; background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
        "        .result-item { margin-bottom: 20px; padding-bottom: 20px; border-bottom: 1px solid #eee; }",
        "        .result-item:last-child { border-bottom: none; }",
        "        .result-title { font-size: 1.2em; margin-bottom: 5px; }",
        "        .result-title a { color: #1a0dab; text-decoration: none; }",
        "        .result-title a:hover { text-decoration: underline; }",
        "        .result-url { font-size: 0.9em; color: #006621; margin-bottom: 5px; word-break: break-all; }",
        "        .result-snippet { font-size: 0.9em; color: #545454; line-height: 1.5; }",
        "        .no-results { text-align: center; color: #888; }",
        "    </style>",
        "</head>",
        "<body>",
        "    <div class=\"container\">",
        f"        <h1>百度搜索结果: {query}</h1>",
    ]

    if not results or (len(results) == 1 and not results[0][0] and not results[0][1] and results[0][2]):
        html_lines.append("        <p class=\"no-results\">没有找到相关结果或页面内容为空。</p>")
    else:
        for idx, (title, url, snippet) in enumerate(results, 1):
            html_lines.append("        <div class=\"result-item\">")
            if title:
                html_lines.append(f"            <h2 class=\"result-title\"><a href=\"{url}\" target=\"_blank\">{title}</a></h2>")
            if url:
                html_lines.append(f"            <p class=\"result-url\">{url}</p>")
            if snippet:
                html_lines.append(f"            <p class=\"result-snippet\">{snippet}</p>")
            html_lines.append("        </div>")

    html_lines.append("    </div>")
    html_lines.append("</body>")
    html_lines.append("</html>")
    return "\n".join(html_lines)

def crawl_baidu(query: str, limit: int = 10, output_format: str = "text") -> Union[str, List[Tuple[str, str, str]]]:
    resp = fetch(query)
    parsed_results = parse_results(resp.text, limit=limit)
    if output_format == "html":
        return to_html(query, parsed_results)
    elif output_format == "text":
        return to_text(parsed_results)
    elif output_format == "json": # For structured data return
        return parsed_results
    else:
        raise ValueError("Invalid output_format. Choose from 'text', 'html', or 'json'.")


