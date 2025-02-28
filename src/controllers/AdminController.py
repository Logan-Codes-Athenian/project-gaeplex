from discord.ext import commands
from services.AdminService import AdminService
from time import gmtime, strftime
import settings as settings

class AdminController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_service = AdminService()
        
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx):
        success = self.admin_service.update_google_sheets()
        if success:
            await ctx.send(f"Backup Successful :)")
        else:
            await ctx.send(f"Backup Failed :(")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def download(self, ctx):
        success = self.admin_service.download_google_sheets()
        if success:
            await ctx.send(f"Download Successful :)")
        else:
            await ctx.send(f"Download Failed :(")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def pause(self, ctx):
        # Resolve the channel
        channel_id = settings.MovementsChannel
        channel = self.bot.get_channel(channel_id)

        if not channel:
            await ctx.send(f"Could not find Movements Channel, check the Channel ID?\nChannel ID in bot: {channel_id}")
            return

        success = self.admin_service.change_game_status("Paused")
        if success:
            await ctx.send(f"Pause Successful :)")
            await channel.send(f"Game Paused @{strftime('%a, %d %b %Y %H:%M:%S +0000', gmtime())}")
        else:
            await ctx.send(f"Pause Failed :(")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unpause(self, ctx):
        # Resolve the channel
        channel_id = settings.MovementsChannel
        channel = self.bot.get_channel(channel_id)

        if not channel:
            await ctx.send(f"Could not find Movements Channel, check the Channel ID?\nChannel ID in bot: {channel_id}")
            return

        success = self.admin_service.change_game_status("Unpaused")
        if success:
            await ctx.send(f"Unpause Successful :)")
            await channel.send(f"Game Unpaused @{strftime('%a, %d %b %Y %H:%M:%S +0000', gmtime())}")
        else:
            await ctx.send(f"Unpause Failed :(")

async def setup(bot):
    await bot.add_cog(AdminController(bot))