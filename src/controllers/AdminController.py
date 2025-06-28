from discord.ext import commands
from services.AdminService import AdminService
from time import gmtime, strftime
import settings as settings
from utils.misc.TemplateUtils import TemplateUtils
from utils.misc.CollectionUtils import CollectionUtils

class AdminController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_service = AdminService()
        self.template_utils     = TemplateUtils()
        self.collection_utils   = CollectionUtils()
        
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
        channel = await self.bot.fetch_channel(channel_id)

        if not channel:
            await ctx.send(f"Could not find Movements Channel, check the Channel ID?\nChannel ID in bot: {channel_id}")
            return

        success = self.admin_service.change_game_status("Paused")
        if success:
            await ctx.send(f"Pause Successful :)")
            await channel.send(f"```Game Paused @{strftime('%a, %d %b %Y %H:%M:%S +0000', gmtime())}```")
            self.admin_service.update_google_sheets() # Updates Game Progress on Pause.
        else:
            await ctx.send(f"Pause Failed :(")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unpause(self, ctx):
        # Resolve the channel
        channel_id = settings.MovementsChannel
        channel = await self.bot.fetch_channel(channel_id)

        if not channel:
            await ctx.send(f"Could not find Movements Channel, check the Channel ID?\nChannel ID in bot: {channel_id}")
            return

        success = self.admin_service.change_game_status("Unpaused")
        if success:
            await ctx.send(f"Unpause Successful :)")
            await channel.send(f"```Game Unpaused @{strftime('%a, %d %b %Y %H:%M:%S +0000', gmtime())}```")
        else:
            await ctx.send(f"Unpause Failed :(")

    @commands.command(name="current-season")
    async def current_season(self, ctx):
        embed_result = self.admin_service.get_current_season_embed()
        if embed_result is None:
            await ctx.send("Could not determine the current season.")
            return

        await ctx.send(embed=embed_result)

    @commands.command(name="change-season")
    @commands.has_permissions(administrator=True)
    async def change_season(self, ctx, season):
        # Resolve the channel
        channel_id = settings.MovementsChannel
        channel = await self.bot.fetch_channel(channel_id)

        if not channel:
            await ctx.send(f"Could not find Movements Channel, check the Channel ID?\nChannel ID in bot: {channel_id}")
            return

        success = self.admin_service.change_season(season)
        if success:
            await ctx.send(f"Season Change Successful :)")
            await channel.send(f"```Season Changed to {season}, @{strftime('%a, %d %b %Y %H:%M:%S +0000', gmtime())}```")
        else:
            await ctx.send(f"Season Change Failed :(")

    @commands.command(name="custom-movement-times")
    @commands.has_permissions(administrator=True)
    async def update_custom_season(self, ctx):
        template = await self.collection_utils.ask_question(
            ctx, self.bot,
            "**Send me the Custom Season Template now Pookie, Grrrr.**", str
        )
        if template is None:
            await ctx.send("No Template Provided.")
            return

        try:
            custom_times = self.template_utils.parse_custom_season_template(template)
        except ValueError:
            await ctx.send("Template incorrect.")
            return 
        
        success = await self.admin_service.update_custom_season_with_template(custom_times)
        if success is None:
            await ctx.send("Could not update Custom Season Movement Times.")
            return

        await ctx.send("Custom Season Movement Times updated.")

async def setup(bot):
    await bot.add_cog(AdminController(bot))