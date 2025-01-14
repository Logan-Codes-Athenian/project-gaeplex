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

    @commands.command()
    async def movements(self, ctx):
        if ctx.author.guild_permissions.administrator:
            movements = self.movement_service.retrieve_all_movements()
        else:
            movements = self.movement_service.retrieve_user_movements(f"<@{ctx.message.author.id}>")

        if not movements:
            await ctx.send("**ruh roh raggy, something was fucked up bruh**")
        else:
            await ctx.send(movements)

    @commands.command()
    async def retrieve(self, ctx, uid):
        if ctx.author.guild_permissions.administrator:
            movement = self.movement_service.retrieve_movement(uid)
        else:
            movement = self.movement_service.retrieve_user_movement(uid, f"<@{ctx.message.author.id}>")

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