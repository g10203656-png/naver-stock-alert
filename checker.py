import os
import re
import requests

PRODUCTS = [
    {
        "id": "13088006935",
        "name": "상품 1",
        "url": "https://smartstore.naver.com/gsc_korea_dt_bh/products/13088006935",
    },
    {
        "id": "13087763836",
        "name": "상품 2",
        "url": "https://smartstore.naver.com/gsc_korea_dt_pw/products/13087763836",
    },
    {
        "id": "13088812913",
        "name": "상품 3",
        "url": "https://brand.naver.com/goodsmilekr/products/13088812913",
    },
]

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram 설정이 없습니다.")
        return

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": True,
        },
        timeout=15,
    )

    response.raise_for_status()


def check_product(product):
    response = requests.get(
        product["url"],
        headers=HEADERS,
        timeout=20,
    )
    response.raise_for_status()

    html = response.text

    soldout_patterns = [
        r'"saleStatus"\s*:\s*"OUTOFSTOCK"',
        r'"saleStatus"\s*:\s*"SOLD_OUT"',
        r'"stockQuantity"\s*:\s*0',
        r'"soldOut"\s*:\s*true',
        r'"isSoldOut"\s*:\s*true',
    ]

    available_patterns = [
        r'"saleStatus"\s*:\s*"ON_SALE"',
        r'"saleStatus"\s*:\s*"SALE"',
        r'"soldOut"\s*:\s*false',
        r'"isSoldOut"\s*:\s*false',
    ]

    for pattern in soldout_patterns:
        if re.search(pattern, html, re.I):
            return False

    for pattern in available_patterns:
        if re.search(pattern, html, re.I):
            return True

    print(f"[판단불가] {product['name']} ({product['id']})")
    return None


def main():
    available = []

    for product in PRODUCTS:
        try:
            result = check_product(product)

            if result is True:
                print(f"[구매가능] {product['name']}")
                available.append(product)

            elif result is False:
                print(f"[품절] {product['name']}")

        except Exception as e:
            print(f"[오류] {product['name']}: {e}")

    if available:
        message = "🚨 네이버스토어 품절 해제!\n\n"

        for product in available:
            message += (
                f"✅ {product['name']}\n"
                f"{product['url']}\n\n"
            )

        send_telegram(message)


if __name__ == "__main__":
    main()
