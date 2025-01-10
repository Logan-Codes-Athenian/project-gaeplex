import discord

class EmbedUtils:
    def __init__(self):
        pass

    def set_info_embed_from_list(self, column_headings, data):
        embedded_message = discord.Embed(
                        title=data[0],
                        description="Super Sexy Embed by Athenian.",
                        color=discord.Color.dark_red())
        
        for i in range(1, len(column_headings)):
            if (column_headings[i] == "Image URL"):
                embedded_message.set_image(url=data[i])
            else:
                embedded_message.add_field(name=column_headings[i], value=data[i], inline=False)
        
        return embedded_message