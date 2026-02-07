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
SERVICE_ROLE_ID = int(os.getenv("SERVICE_ROLE_ID"))

# 팀 설정
TEAMS = {
    "infra": {
        "tag": "[Infra]",
        "role_id": INFRA_ROLE_ID,
    },
    "service": {
        "tag": "[Service]",
        "role_id": SERVICE_ROLE_ID,
    }
}

# =====================
# 디스코드 클라이언트
# =====================
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# =====================
# 스케줄러 (KST)
# =====================
scheduler = AsyncIOScheduler(timezone="Asia/Seoul")


# =====================
# 오늘 일일회고 스레드 생성
# =====================
async def create_daily_retrospectives():
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Channel not found")
        return

    today_display = datetime.now().strftime("%Y / %m / %d")

    for team in TEAMS.values():
        base_message = await channel.send(
            f"<@&{team['role_id']}> 금일 일일회고 스레드입니다",
            allowed_mentions=discord.AllowedMentions(roles=True)
        )

        await base_message.create_thread(
            name=f"{team['tag']} 일일회고 - {today_display}",
            auto_archive_duration=1440
        )

        print(f"✅ {team['tag']} thread created: {today_display}")


# =====================
# 어제 일일회고 스레드 닫기
# =====================
async def close_yesterday_retrospectives():
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Channel not found")
        return

    yesterday_display = (datetime.now() - timedelta(days=1)).strftime("%Y / %m / %d")
    target_names = {
        f"{team['tag']} 일일회고 - {yesterday_display}"
        for team in TEAMS.values()
    }

    async for message in channel.history(limit=100):
        if message.author == client.user and message.thread:
            if message.thread.name in target_names:
                await message.thread.edit(archived=True)
                print(f"🧵 Archived: {message.thread.name}")


# =====================
# 봇 준비 완료
# =====================
@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")

    # 17:59 → 전날 스레드 닫기
    scheduler.add_job(
        close_yesterday_retrospectives,
        trigger="cron",
        hour=17,
        minute=59
    )

    # 18:00 → 오늘 스레드 생성
    scheduler.add_job(
        create_daily_retrospectives,
        trigger="cron",
        hour=18,
        minute=0
    )

    scheduler.start()


# =====================
# 봇 실행
# =====================
client.run(TOKEN)
