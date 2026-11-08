import os
import asyncio
from fastapi import FastAPI, HTTPException, Header # pyright: ignore[reportMissingImports]
from pydantic import BaseModel # pyright: ignore[reportMissingImports]
import discord # pyright: ignore[reportMissingImports]
from dotenv import load_dotenv # type: ignore
import uvicorn # pyright: ignore[reportMissingImports]

load_dotenv()
# .env から捨て垢のトークンを読み込む
TOKEN = os.getenv("DISCORD_TOKEN")
SECRET_KEY = os.getenv("CLOUDFLARE_SECRET_KEY", "my_super_secret_key")

# ---------------------------------------------------------------------------
# セルフボット（一般ユーザーアカウント）の初期化
# ---------------------------------------------------------------------------
from discord import Intents 

intents = Intents.all()
client = discord.Client(intents=intents, bot=False)
# ---------------------------------------------------------------------------
# FastAPI (Cloudflareからの潜入命令を待つ窓口)
# ---------------------------------------------------------------------------
app = FastAPI()

class JoinRequest(BaseModel):
    channel_id: int

@client.event
async def on_ready():
    print(f"【セルフボット】捨て垢（{client.user}）でログインしました。待機中...")

@app.post("/api/join")
async def web_join_vc(data: JoinRequest, x_secret_key: str = Header(None)):
    """Cloudflareから届くVC潜入命令を処理するAPI"""
    if x_secret_key != SECRET_KEY:
        raise HTTPException(status_code=403, detail="認証エラーが発生しました。トークンが初期化されていませんか？")

    channel = client.get_channel(data.channel_id)
    if channel and isinstance(channel, discord.VoiceChannel):
        asyncio.create_task(channel.connect(self_mute=True, self_deaf=True))
        print(f"【ステルス潜入】{channel.guild.name} ＞ {channel.name} に入室します。")
        return {"status": "success", "message": "無事に潜入を開始しました。"}
        
    raise HTTPException(status_code=404, detail="問題が発生しました:VCが見つかりません。")

# ---------------------------------------------------------------------------
# 同時起動メイン処理
# ---------------------------------------------------------------------------
async def main():
    port = int(os.getenv("PORT", 8000))
    config = uvicorn.Config(app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    
    # Webサーバーと捨て垢ログインを同時に並行稼働
    await asyncio.gather(
        server.serve(),
        client.start(TOKEN, bot=False)
    )

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError("DISCORD_TOKEN が設定されていません。")
    asyncio.run(main())
