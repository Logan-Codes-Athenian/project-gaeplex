from discord.ext import commands
from services.AdminService import AdminService

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

async def setup(bot):
    await bot.add_cog(AdminController(bot))