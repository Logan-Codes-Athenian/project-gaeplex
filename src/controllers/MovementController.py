from discord.ext import commands
from services.MovementService import MovementService

class MovementController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.movement_service = MovementService(bot)

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def movement(self, ctx):
        success = await self.movement_service.create_template_movement(ctx)
        if not success:
            await ctx.send("**You gone fucked up cuh**")
        else:
            await ctx.send("**Success! Good Boy :)**")

async def setup(bot):
    await bot.add_cog(MovementController(bot))