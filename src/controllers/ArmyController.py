from discord.ext import commands
from services.ArmyService import ArmyService

class ArmyController(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.army_service = ArmyService(bot)

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def army(self, ctx):
        success, army_uid = await self.army_service.create_template_army(ctx)
        if not success:
            await ctx.send("**Failure :( Check the Template is correct.**")
        else:
            await ctx.send(f"**Success, Army ID: {army_uid} Created! :)**")

    @commands.command()
    async def armies(self, ctx):
        if ctx.author.guild_permissions.administrator:
            armies = self.army_service.retrieve_all_armies()
        else:
            armies = self.army_service.retrieve_user_armies(f"<@{ctx.message.author.id}>")

        if not armies:
            await ctx.send("**Couldn't find any armies o.O**")
        else:
            await ctx.send(armies)

    @commands.command(name="retrieve-army")
    async def retrieve(self, ctx, uid):
        if ctx.author.guild_permissions.administrator:
            army = self.army_service.retrieve_army(uid)
        else:
            army = self.army_service.retrieve_user_army(uid, f"<@{ctx.message.author.id}>")

        if not army:
            await ctx.send("**You sure thats an army pookie? Check the UID again.**")
        else:
            await ctx.send(embed=army)

    @commands.has_permissions(administrator=True)
    @commands.command()
    async def delete(self, ctx, uid):
        success = self.army_service.delete_army(uid)
        if not success:
            await ctx.send("**Something went wrong...**")
        else:
            await ctx.send("**Army Deletion success! :)**")

    @commands.has_permissions(administrator=True)
    @commands.command(name="army-status")
    async def status(self, ctx, uid, status):
        status_changed = self.army_service.change_army_status(uid, status)
        if not status_changed:
            await ctx.send("status change failed.")
            return
        
        await ctx.send("Status Change Completed!")

async def setup(bot):
    await bot.add_cog(ArmyController(bot))