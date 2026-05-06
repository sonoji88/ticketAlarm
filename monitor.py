import requests
import os
from datetime import datetime

# ─────────────────────────────────────────
#  설정값
# ─────────────────────────────────────────
GOODS_CODE = "26005547"
PERF_URL   = f"https://tickets.interpark.com/goods/{GOODS_CODE}"
BASE_URL   = "https://api-ticketfront.interpark.com"

BOT_TOKEN  = os.environ["BOT_TOKEN"]
CHAT_ID    = os.environ["CHAT_ID"]

# 모니터링할 날짜 (YYYYMMDD)
PLAY_DATES = ["20260613"]

# ─────────────────────────────────────────
#  헤더 (sec-ch-ua 없으면 403)
# ─────────────────────────────────────────
HEADERS = {
    "sec-ch-ua-platform": '"macOS"',
    "referer": "https://tickets.interpark.com/",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/141.0.0.0 Safari/537.36"
    ),
    "accept": "application/json, text/plain, */*",
    "sec-ch-ua": '"HeadlessChrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    "accept-language": "ko-KR,ko;q=0.9",
    "sec-ch-ua-mobile": "?0",
}

# ─────────────────────────────────────────
#  잔여석 조회
# ─────────────────────────────────────────
def check_remain(play_date: str):
    url = f"{BASE_URL}/v1/goods/{GOODS_CODE}/playSeq/PlayDate/{play_date}/ALL"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("remainSeat", [])
    except Exception as e:
        print(f"[오류] {play_date} 조회 실패: {e}")
        return None

# ─────────────────────────────────────────
#  텔레그램 알림
# ─────────────────────────────────────────
def send_telegram(message: str):
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": message},
            timeout=10,
        )
        resp.raise_for_status()
        print("✅ 텔레그램 알림 전송 완료")
    except Exception as e:
        print(f"[오류] 텔레그램 전송 실패: {e}")

# ─────────────────────────────────────────
#  메인
# ─────────────────────────────────────────
def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 취소표 확인 시작")
    available_list = []

    for date in PLAY_DATES:
        remain = check_remain(date)
        formatted = f"{date[:4]}년 {date[4:6]}월 {date[6:]}일"

        if remain is None:
            print(f"  [{formatted}] 조회 실패 (스킵)")
            continue

        print(f"  [{formatted}] remainSeat: {remain}")

        if len(remain) > 0:
            seats_text = "\n".join([
                f"  ✅ {r.get('playSeqName', '회차')} — 잔여 {r.get('remainCnt', '?')}석"
                for r in remain
            ])
            available_list.append(f"📅 {formatted}\n{seats_text}")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if available_list:
        msg = "🚨 인터파크 취소표 발생!\n\n"
        msg += "\n\n".join(available_list)
        msg += f"\n\n🔗 {PERF_URL}"
        send_telegram(msg)
    else:
        msg = f"🔍 [{now}] 확인 완료\n매진 상태입니다. 취소표 없음."
        send_telegram(msg)
        print("  → 모두 매진 상태.")

    print("확인 완료.")

if __name__ == "__main__":
    main()
