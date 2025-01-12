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

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def movements(self, ctx):
        movements = self.movement_service.retrieve_all_movements()
        if not movements:
            await ctx.send("**Something funky, idk?**")
        else:
            await ctx.send(movements)

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def retrieve(self, ctx, uid):
        movement = self.movement_service.retrieve_movement(uid)
        if not movement:
            await ctx.send("**You sure thats a movement pookie? 8==)**")
        else:
            await ctx.send(embed=movement)

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def retreat(self, ctx, uid):
        success = self.movement_service.retreat_movement(uid)
        if not success:
            await ctx.send("**You gone fucked up cuh**")
        else:
            await ctx.send("**Successfully Retreated Movement :)**")

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def cancel(self, ctx, uid):
        success = self.movement_service.cancel_movement(uid)
        if not success:
            await ctx.send("**You gone fucked up cuh**")
        else:
            await ctx.send("**Cancelled Movement :)**")

async def setup(bot):
    await bot.add_cog(MovementController(bot))