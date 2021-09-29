import os
import discord 
from discord.ext import commands, tasks
from discord.voice_client import VoiceClient
import nacl
import asyncio
import youtube_dl
from keep_alive import keep_alive


from random import choice

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

client = commands.Bot(command_prefix = '-')

status = ['Playing music!', 'chilling...', 'sleeping...']

#EVENTS
@client.event
async def on_ready():
    change_status.start()
    print("Bot is online!")

@client.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='general')
    await channel.send(f'Welcome {member.mention}! See `-help` for the commands list.')


#BASIC COMMANDS
@client.command(name = 'ping', help='This command returns the latency')
async def ping(ctx):
    await ctx.send(f'**Ping!** Latency: {round(client.latency * 1000)}ms')

@client.command(name = 'hello', help ='This command returns a welcome message')
async def hello(ctx):
    greetings = ['Howdy!', 'Wassuuuuuuuuuuup!', 'Hey boss', 'Coming up with more greetings...']
    await ctx.send(choice(greetings))

@client.command(name = 'credits', help='This commands shows the credits')
async def credits(ctx):
    await ctx.send('Your one and only **programmer overlord** `DAN`')



#MUSIC COMMANDS
@client.command(name = 'play', help='This commands plays a song')
async def play(ctx, url):
  #if not in a voice channel, dont connect the bot to the channel
    if not ctx.message.author.voice:
        await ctx.send('You are not connected to a voice channel')
        return
    else:
      #if connected to a voice channel, save in variable channel which voice channel the person who wrote the command is in
        channel = ctx.message.author.voice.channel
    
    #connect to the voice channel defined above
    await channel.connect()

    server = ctx.message.guild
    #the voice channel we are currently in
    voice_channel = server.voice_client

    async with ctx.typing():
      #TEMPORARY, make it so if not a youtube link, it doesnt get stuck and we can make it leave
      if "youtube" not in url: 
        return
      else:
        player = await YTDLSource.from_url(url, loop=client.loop)
        voice_channel.play(player, after=lambda e: print('Player error: %s' %e) if e else None)
        await ctx.send('**Now playing:** {}'.format(player.title))

@client.command(name = 'stop', help='This commands stops the song and makes bot leave')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
      await voice_client.disconnect()
    else:
      await ctx.send("The bot isn't connected bozo!")
    
#PAUSE
@client.command(name = 'pause', help='This command pauses the music')
async def pause(ctx):
  voice = discord.utils.get(client.voice_clients, guild = ctx.guild)
  if voice.is_playing():
    voice.pause()
  else:
    await ctx.send("There's nothing to pause babycakes")

#RESUME
@client.command(name = 'resume', help='This command resumes paused music')
async def resume(ctx):
  voice = discord.utils.get(client.voice_clients, guild = ctx.guild)
  if voice.is_paused():
    voice.resume()
  else:
    await ctx.send("There's nothing to resume babycakes")

####

@tasks.loop(seconds = 20)
async def change_status():
    await client.change_presence(activity = discord.Game(choice(status)))


keep_alive()

token = os.environ['TOKEN']
client.run(token)