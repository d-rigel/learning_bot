import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
from utils.course_manager import get_courses, create_profile, next_session, get_current_session
from utils.profile_manager import get_profile, save_profile
from utils.intent_detector import generate_response

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        await handle_dm(message)
    else:
        await bot.process_commands(message)

async def handle_dm(message):
    content = message.content.strip().lower()
    discord_id = message.author.id
    profile = get_profile(discord_id)

    async with message.channel.typing():
        if content == "menu":
            await display_menu(message.author)
        elif content.startswith("a"):
            courses = get_courses()
            await message.author.send(f"I offer courses in {', '.join(courses)}. Which one would you like to start with?")
        elif content.startswith("b"):
            if len(content.split()) < 2:
                await message.author.send("Please specify a course to enroll in. For example: 'b JavaScript'")
            else:
                course = content.split(" ")[1]
                profile = create_profile(discord_id, course)
                save_profile(discord_id, profile)  # Save the profile after enrolling
                await message.author.send(f"You're enrolled in the {course} course! Let's begin with your first session.")
                await send_next_session(message.author, profile)
        elif content == "c":
            if profile:
                await send_next_session(message.author, profile)
            else:
                await message.author.send("You are not enrolled in any course. Please enroll in a course first.")
        elif content == "d":
            if profile:
                session = get_current_session(profile)
                task = session["tasks"][0]
                await message.author.send(f"Task: {task}")
                await message.author.send("Type 'e <your response>' to check your task.")
            else:
                await message.author.send("You are not enrolled in any course. Please enroll in a course first.")
        elif content.startswith("e"):
            if len(content.split()) < 3:
                await message.author.send("Please provide a response to check. For example: 'e let x = 10;'")
            else:
                response_text = content.split(" ", 2)[2]
                if profile:
                    session = get_current_session(profile)
                    expected_intent = session["tasks"][0]
                    user_input = f"detect_intent response_text='{response_text}' expected_intent='{expected_intent}'"
                    response = generate_response(user_input)
                    await message.author.send(response)
                    if "Great job!" in response:
                        await send_next_session(message.author, profile)
                else:
                    await message.author.send("You are not enrolled in any course. Please enroll in a course first.")
        elif content == "next":
            if profile:
                await send_next_session(message.author, profile)
            else:
                await message.author.send("You are not enrolled in any course. Please enroll in a course first.")
        elif content == "end":
            if profile:
                await message.author.send("You have ended the current session. Type 'menu' to see available options.")
            else:
                await message.author.send("You are not enrolled in any course. Please enroll in a course first.")
        else:
            await message.author.send("I didn't understand that. Please use the 'menu' command to see available options.")

async def send_next_session(user, profile):
    async with user.typing():
        session = next_session(profile)
        content = session["content"]
        examples = "\n".join(session["examples"])
        await user.send(f"Session Name: {session['name']}\nContent: {content}\nExamples:\n{examples}")
        await user.send("Type 'next' to proceed to the next session or 'end' to end the current session.")
        save_profile(user.id, profile)  # Save the profile after starting a new session

async def display_menu(user):
    async with user.typing():
        menu = (
            "Please select an option by typing the corresponding letter:\n"
            "a) List Courses\n"
            "b) Enroll in a Course\n"
            "c) Start Session\n"
            "d) Assign Task\n"
            "e) Check Task"
        )
        await user.send(menu)

bot.run(os.getenv('DISCORD_BOT_TOKEN'))





# import discord
# from discord.ext import commands
# from dotenv import load_dotenv
# import os
# from utils.course_manager import get_courses, create_profile, next_session, get_current_session
# from utils.profile_manager import get_profile, save_profile
# from utils.intent_detector import detect_intent

# load_dotenv()

# intents = discord.Intents.default()
# intents.message_content = True

# bot = commands.Bot(command_prefix="!", intents=intents)

# @bot.event
# async def on_ready():
#     print(f'Logged in as {bot.user}')

# @bot.event
# async def on_message(message):
#     if message.author == bot.user:
#         return

#     if isinstance(message.channel, discord.DMChannel):
#         await handle_dm(message)
#     else:
#         await bot.process_commands(message)

# async def handle_dm(message):
#     content = message.content.strip().lower()
#     discord_id = message.author.id
#     profile = get_profile(discord_id)

#     async with message.channel.typing():
#         if content == "menu":
#             await display_menu(message.author)
#         elif content.startswith("a"):
#             courses = get_courses()
#             await message.author.send(f"I offer courses in {', '.join(courses)}. Which one would you like to start with?")
#         elif content.startswith("b"):
#             if len(content.split()) < 2:
#                 await message.author.send("Please specify a course to enroll in. For example: 'b JavaScript'")
#             else:
#                 course = content.split(" ")[1]
#                 profile = create_profile(discord_id, course)
#                 save_profile(discord_id, profile)  # Save the profile after enrolling
#                 await message.author.send(f"You're enrolled in the {course} course! Let's begin with your first session.")
#                 await send_next_session(message.author, profile)
#         elif content == "c":
#             if profile:
#                 await send_next_session(message.author, profile)
#             else:
#                 await message.author.send("You are not enrolled in any course. Please enroll in a course first.")
#         elif content == "d":
#             if profile:
#                 session = get_current_session(profile)
#                 task = session["tasks"][0]
#                 await message.author.send(f"Task: {task}")
#                 await message.author.send("Type 'e <your response>' to check your task.")
#             else:
#                 await message.author.send("You are not enrolled in any course. Please enroll in a course first.")
#         elif content.startswith("e"):
#             if len(content.split()) < 3:
#                 await message.author.send("Please provide a response to check. For example: 'e let x = 10;'")
#             else:
#                 response_text = content.split(" ", 2)[2]
#                 if profile:
#                     session = get_current_session(profile)
#                     expected_intent = session["tasks"][0]
#                     is_correct, feedback = detect_intent(response_text, expected_intent)
#                     await message.author.send(feedback)
#                     if is_correct:
#                         await send_next_session(message.author, profile)
#                 else:
#                     await message.author.send("You are not enrolled in any course. Please enroll in a course first.")
#         elif content == "next":
#             if profile:
#                 await send_next_session(message.author, profile)
#             else:
#                 await message.author.send("You are not enrolled in any course. Please enroll in a course first.")
#         elif content == "end":
#             if profile:
#                 await message.author.send("You have ended the current session. Type 'menu' to see available options.")
#             else:
#                 await message.author.send("You are not enrolled in any course. Please enroll in a course first.")
#         else:
#             await message.author.send("I didn't understand that. Please use the 'menu' command to see available options.")

# async def send_next_session(user, profile):
#     async with user.typing():
#         session = next_session(profile)
#         content = session["content"]
#         examples = "\n".join(session["examples"])
#         await user.send(f"Session Name: {session['name']}\nContent: {content}\nExamples:\n{examples}")
#         await user.send("Type 'next' to proceed to the next session or 'end' to end the current session.")
#         save_profile(user.id, profile)  # Save the profile after starting a new session

# async def display_menu(user):
#     async with user.typing():
#         menu = (
#             "Please select an option by typing the corresponding letter:\n"
#             "a) List Courses\n"
#             "b) Enroll in a Course\n"
#             "c) Start Session\n"
#             "d) Assign Task\n"
#             "e) Check Task"
#         )
#         await user.send(menu)

# bot.run(os.getenv('DISCORD_BOT_TOKEN'))

