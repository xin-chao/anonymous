import json
import os

import feedparser
import requests
from requests_oauthlib import OAuth1

import gemini


def is_proceeded(url):
    kv_origin = os.getenv("KV_ORIGIN")
    proceeded = requests.get(f"{kv_origin}/hatena/{url}").text
    if proceeded:
        return True
    requests.put(f"{kv_origin}/hatena/{url}", "1")
    return False


def post_comment(url, comment):
    print(url, comment)
    client_key, client_secret, token_key, token_secret = os.getenv(
        "HATENA_TOKEN"
    ).split(",")
    requests.post(
        "https://bookmark.hatenaapis.com/rest/1/my/bookmark",
        {"url": url, "comment": comment},
        auth=OAuth1(client_key, client_secret, token_key, token_secret),
    )


entries = []
for entry in feedparser.parse("https://anond.hatelabo.jp/rss").entries:
    if "anond:" in entry.title:
        continue
    if is_proceeded(entry.link):
        continue
    if "グエン大好き" in entry.content[0].value:
        continue
    if len(entry.content[0].value) < 100:
        print("short content", len(entry.content[0].value))
        continue
    title = "" if entry.title == "■" else f"<h1>{entry.title}</h1>"
    html = title + entry.content[0].value
    entries.append({"url": entry.link, "html": html})

if entries:
    print("ENTRIES:", len(entries))
    context = json.dumps(entries, ensure_ascii=False)
    response = gemini.generate_content(context)
    urls = [entry["url"] for entry in entries]
    for comment in response.parsed:
        if comment["url"] not in urls:
            print("NOT_IN_URLS:", comment["url"])
            continue
        if comment["is_inappropriate"]:
            print("IS_INAPPROPRIATE:", comment)
            continue
        if comment["predicted_hatebu_count"] < 70:
            print("PREDICTED_HATEBU_COUNT:", comment)
            continue
        prohibited_keywords = ["有料", "閲覧", "エラー", "要望"]
        if any(keyword in comment["comment"] for keyword in prohibited_keywords):
            print("PROHIBITED_KEYWORDS:", comment)
            continue
        post_comment(comment["url"], comment["comment"])
