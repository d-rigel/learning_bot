import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from utils.course_manager import get_courses, create_profile, next_session
from utils.profile_manager import get_profile
from utils.intent_detector import detect_intent

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def list_courses(ctx):
    courses = get_courses()
    await ctx.send(f"I offer courses in {', '.join(courses)}. Which one would you like to start with?")

@bot.command()
async def enroll(ctx, course):
    discord_id = ctx.author.id
    profile = create_profile(discord_id, course)
    await ctx.send(f"You're enrolled in the {course} course! Let's begin with your first session.")

@bot.command()
async def start_session(ctx):
    discord_id = ctx.author.id
    profile = get_profile(discord_id)
    session = next_session(profile)
    content = session["content"]
    examples = "\n".join(session["examples"])
    await ctx.send(f"{content}\n\nExamples:\n{examples}")

@bot.command()
async def assign_task(ctx):
    discord_id = ctx.author.id
    profile = get_profile(discord_id)
    session = next_session(profile)
    print(profile)
    task = session["tasks"][0]
    await ctx.send(f"Task: {task}")

@bot.command()
async def check_task(ctx, *, response_text):
    discord_id = ctx.author.id
    profile = get_profile(discord_id)
    session = next_session(profile)
    expected_intent = session["tasks"][0]
    if detect_intent(response_text, expected_intent):
        await ctx.send("Great job! You correctly completed the task. Let's move on to the next task.")
    else:
        await ctx.send("It looks like there's an error. Remember to follow the task instructions. Try again!")

bot.run(os.getenv('DISCORD_BOT_TOKEN'))