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

    @commands.command(name="retrieve-movement")
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

    @commands.command()
    async def path(self, ctx, origin, destination):
        path, time = await self.movement_service.retrieve_path(ctx, origin, destination, None)
        if not path:
            await ctx.send("**Stop being retarded, bad player, bad! :(**")
        else:
            await ctx.send(f"**Fastest Path and ETC for {origin} -> {destination}**\n"
                        f"*Fastest Path: {path}*\n"
                        f"*Estimated Time to Completion: {time} minutes*")

    @commands.command()
    async def hex(self, ctx, hex):
        info = self.movement_service.retrieve_hex_info(hex)
        if not info:
            await ctx.send("**I don't think that's a hex baka!**")
        else:
            await ctx.send(embed = info)

async def setup(bot):
    await bot.add_cog(MovementController(bot))