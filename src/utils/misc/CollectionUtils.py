import discord

class CollectionUtils:

    @staticmethod
    async def ask_question(ctx, bot, question, return_type, timeout=60):
        await ctx.send(question)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            # Wait for a response from the user
            message = await bot.wait_for('message', timeout=timeout, check=check)
            # Validate and convert the response
            try:
                response = return_type(message.content)
                return response
            except ValueError:
                await ctx.send(f"Invalid input. Expected a value of type {return_type.__name__}.")
                return None
        except discord.TimeoutError:
            await ctx.send("Timed out waiting for a response.")
            return None