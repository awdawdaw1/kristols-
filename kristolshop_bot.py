import discord
from discord.ext import commands
import asyncio
import random
import aiosqlite
import os
from dotenv import load_dotenv

# Загружаем токен из .env файла
load_dotenv("C:/Users/admin/KristolShopBot/.env")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

DB_PATH = "C:/Users/admin/KristolShopBot/economy.db"

async def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            wallet INTEGER DEFAULT 0,
            bank INTEGER DEFAULT 0
        )
        """)
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT wallet, bank FROM users WHERE user_id = ?", (str(user_id),)) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0], row[1]
            else:
                await db.execute("INSERT INTO users (user_id) VALUES (?)", (str(user_id),))
                await db.commit()
                return 0, 0

async def update_balance(user_id, wallet_delta=0, bank_delta=0):
    async with aiosqlite.connect(DB_PATH) as db:
        wallet, bank = await get_user(user_id)
        wallet += wallet_delta
        bank += bank_delta
        await db.execute("REPLACE INTO users (user_id, wallet, bank) VALUES (?, ?, ?)", (str(user_id), wallet, bank))
        await db.commit()

@bot.command(name="balance", aliases=["баланс"])
async def balance(ctx):
    wallet, bank = await get_user(ctx.author.id)
    embed = discord.Embed(title="💰 Ваш баланс", color=discord.Color.blue())
    embed.add_field(name="Кошелёк", value=f"{wallet} монет", inline=True)
    embed.add_field(name="Банк", value=f"{bank} монет", inline=True)
    await ctx.send(embed=embed)

@bot.command(name="work", aliases=["работа"])
async def work(ctx):
    earnings = random.randint(50, 150)
    await update_balance(ctx.author.id, wallet_delta=earnings)
    await ctx.send(f"💼 {ctx.author.mention}, вы заработали {earnings} монет!")

@bot.command(name="rob", aliases=["грабить"])
async def rob(ctx, target: discord.Member):
    if target.id == ctx.author.id:
        return await ctx.send("😒 Себя грабить нельзя.")

    success = random.choice([True, False])
    amount = random.randint(30, 100)

    attacker_wallet, _ = await get_user(ctx.author.id)
    victim_wallet, _ = await get_user(target.id)

    if success and victim_wallet >= amount:
        await update_balance(ctx.author.id, wallet_delta=amount)
        await update_balance(target.id, wallet_delta=-amount)
        embed = discord.Embed(title="🚨 Ограбление!", color=discord.Color.red())
        embed.add_field(name="Грабитель", value=ctx.author.mention)
        embed.add_field(name="Жертва", value=target.mention)
        embed.add_field(name="Украдено", value=f"{amount} монет")
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"🚔 {ctx.author.mention}, вас поймали при попытке ограбления!")

@bot.command(name="transfer", aliases=["перевести"])
async def transfer(ctx, target: discord.Member, amount: int):
    if amount <= 0:
        return await ctx.send("Сумма должна быть положительной.")
    sender_wallet, _ = await get_user(ctx.author.id)
    if sender_wallet < amount:
        return await ctx.send("Недостаточно монет.")

    await update_balance(ctx.author.id, wallet_delta=-amount)
    await update_balance(target.id, wallet_delta=amount)
    await ctx.send(f"💸 {ctx.author.mention} перевёл {amount} монет {target.mention}.")

@bot.command(name="bank")
async def bank(ctx, action: str, amount: int):
    wallet, bank = await get_user(ctx.author.id)
    if action == "deposit":
        if amount > wallet:
            return await ctx.send("Недостаточно монет в кошельке.")
        await update_balance(ctx.author.id, wallet_delta=-amount, bank_delta=amount)
        await ctx.send(f"🏦 Вы положили {amount} монет в банк.")
    elif action == "withdraw":
        if amount > bank:
            return await ctx.send("Недостаточно монет в банке.")
        await update_balance(ctx.author.id, wallet_delta=amount, bank_delta=-amount)
        await ctx.send(f"💰 Вы сняли {amount} монет из банка.")
    else:
        await ctx.send("Использование: !bank deposit <сумма> или !bank withdraw <сумма>")

@bot.event
async def on_ready():
    print("✅ Kristol Shop Bot готов к работе!")

async def main():
    try:
        await init_db()
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise ValueError("❌ Токен не найден в .env файле.")
        await bot.start(token)
    except Exception as e:
        print("Ошибка при запуске бота:", e)
        input("Нажмите Enter, чтобы выйти ...")

if __name__ == "__main__":
    asyncio.run(main())



