import os
import discord
from dotenv import load_dotenv
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# =====================
# 환경변수 로드
# =====================
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
INFRA_ROLE_ID = int(os.getenv("INFRA_ROLE_ID"))

TEAM_TAG = "[Infra]"

# =====================
# 디스코드 클라이언트
# =====================
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# =====================
# 스케줄러 (KST 기준)
# =====================
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


# =====================
# 오늘 일일회고 스레드 생성
# =====================
async def create_daily_retrospective():
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Channel not found")
        return

    today_display = datetime.now().strftime("%Y / %m / %d")

    # 1️⃣ 기준 메시지 (공지 + 역할 멘션)
    base_message = await channel.send(
        f"<@&{INFRA_ROLE_ID}> 금일 일일회고 스레드입니다",
        allowed_mentions=discord.AllowedMentions(roles=True)
    )

    # 2️⃣ 스레드 생성 (첫 메시지 없음)
    await base_message.create_thread(
        name=f"{TEAM_TAG} 일일회고 - {today_display}",
        auto_archive_duration=1440  # 24시간
    )

    print(f"✅ Daily retrospective thread created: {today_display}")


# =====================
# 어제 일일회고 스레드 닫기 (아카이브)
# =====================
async def close_yesterday_retrospective():
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Channel not found")
        return

    yesterday_display = (datetime.now() - timedelta(days=1)).strftime("%Y / %m / %d")
    target_thread_name = f"{TEAM_TAG} 일일회고 - {yesterday_display}"

    async for message in channel.history(limit=50):
        if message.author == client.user and message.thread:
            if message.thread.name == target_thread_name:
                await message.thread.edit(archived=True)
                print(f"🧵 Retrospective archived: {yesterday_display}")
                break


# =====================
# 봇 준비 완료 이벤트
# =====================
@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")

    # 매일 17:59 → 어제 스레드 닫기
    scheduler.add_job(
        close_yesterday_retrospective,
        trigger="cron",
        hour=17,
        minute=59
    )

    # 매일 18:00 → 오늘 스레드 생성
    scheduler.add_job(
        create_daily_retrospective,
        trigger="cron",
        hour=18,
        minute=0
    )

    scheduler.start()


# =====================
# 봇 실행
# =====================
client.run(TOKEN)

