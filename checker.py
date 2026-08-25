import os
from playwright.sync_api import sync_playwright

PRODUCTS = [
    {
        "name": "상품 1",
        "url": "https://smartstore.naver.com/gsc_korea_dt_bh/products/13088006935",
    },
    {
        "name": "상품 2",
        "url": "https://smartstore.naver.com/gsc_korea_dt_pw/products/13087763836",
    },
    {
        "name": "상품 3",
        "url": "https://brand.naver.com/goodsmilekr/products/13088812913",
    },
]

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_telegram(request, message):
    response = request.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        form={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": "true",
        },
    )

    if not response.ok:
        raise RuntimeError(
            f"Telegram 전송 실패: {response.status} {response.text()}"
        )


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            locale="ko-KR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )

        page = context.new_page()

        available = []

        for product in PRODUCTS:
            try:
                response = page.goto(
                    product["url"],
                    wait_until="domcontentloaded",
                    timeout=30000,
                )

                if response:
                    print(
                        f"[HTTP {response.status}] "
                        f"{product['name']} - {product['url']}"
                    )

                page.wait_for_timeout(3000)

                body = page.locator("body").inner_text()

                if "429 Too Many Requests" in body:
                    print(f"[429 차단] {product['name']}")
                    continue

                soldout_words = [
                    "품절",
                    "일시품절",
                    "현재 구매할 수 없는 상품",
                ]

                buy_words = [
                    "구매하기",
                    "장바구니",
                ]

                is_soldout = any(word in body for word in soldout_words)
                has_buy = any(word in body for word in buy_words)

                if has_buy and not is_soldout:
                    print(f"[구매가능] {product['name']}")
                    available.append(product)

                elif is_soldout:
                    print(f"[품절] {product['name']}")

                else:
                    print(f"[판단불가] {product['name']}")

            except Exception as e:
                print(f"[오류] {product['name']}: {e}")

        if available:
            message = "🚨 네이버스토어 품절 해제!\n\n"

            for product in available:
                message += (
                    f"✅ {product['name']}\n"
                    f"{product['url']}\n\n"
                )

            send_telegram(context.request, message)

        browser.close()


if __name__ == "__main__":
    main()
