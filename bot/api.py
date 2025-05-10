import os
import discord
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
from discord.ext import commands

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/send-embed")
async def send_embed(title: str = Form(...), description: str = Form(...), channel: str = Form(...)):
    channel_obj = bot.get_channel(int(channel))
    if channel_obj:
        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        await channel_obj.send(embed=embed)
        return {"status": "Embed envoyé"}
    else:
        return {"status": "Salon introuvable"}

@bot.event
async def on_ready():
    print(f'{bot.user} est prêt à recevoir des requêtes API.')

if __name__ == "__main__":
    import threading

    def start_api():
        uvicorn.run(app, host="0.0.0.0", port=5000)

    threading.Thread(target=start_api).start()
    bot.run(TOKEN)
