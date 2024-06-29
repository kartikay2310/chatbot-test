from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity, ActivityTypes, CardAction, ActionTypes, HeroCard, Attachment

class TeamsBot:
    def __init__(self, adapter):
        self.adapter = adapter

    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.text == "start":
            await self.ask_os_details(turn_context)
        elif turn_context.activity.text in ["Windows", "MacOS", "Linux"]:
            await self.ask_driver_details(turn_context)
        elif turn_context.activity.text in ["NVIDIA", "AMD", "Intel"]:
            await self.ask_problem1(turn_context)
        elif turn_context.activity.text in ["Option 1", "Option 2", "Option 3"]:
            await self.ask_problem2(turn_context)
        elif turn_context.activity.text in ["Follow-up Option 1", "Follow-up Option 2", "Follow-up Option 3"]:
            await turn_context.send_activity("Hey, you've reached the end!")

    async def ask_os_details(self, turn_context: TurnContext):
        card = self.create_hero_card("Choose your OS:", ["Windows", "MacOS", "Linux"])
        await turn_context.send_activity(MessageFactory.attachment(card))

    async def ask_driver_details(self, turn_context: TurnContext):
        card = self.create_hero_card("Choose your driver:", ["NVIDIA", "AMD", "Intel"])
        await turn_context.send_activity(MessageFactory.attachment(card))

    async def ask_problem1(self, turn_context: TurnContext):
        card = self.create_hero_card("Problem 1: Choose an option:", ["Option 1", "Option 2", "Option 3"])
        await turn_context.send_activity(MessageFactory.attachment(card))

    async def ask_problem2(self, turn_context: TurnContext):
        card = self.create_hero_card("Problem 2: Choose a follow-up option:", ["Follow-up Option 1", "Follow-up Option 2", "Follow-up Option 3"])
        await turn_context.send_activity(MessageFactory.attachment(card))

    def create_hero_card(self, title, buttons):
        card = HeroCard(
            title=title,
            buttons=[CardAction(type=ActionTypes.im_back, title=button, value=button) for button in buttons]
        )
        return Attachment(content_type="application/vnd.microsoft.card.hero", content=card)

async def handle_activity(request):
    body = await request.json()
    activity = Activity().deserialize(body)
    auth_header = request.headers.get("Authorization", "")
    bot = TeamsBot(adapter)
    await adapter.process_activity(activity, auth_header, bot.on_message_activity)
    return web.Response(status=200)

APP_ID = "your_app_id"
APP_PASSWORD = "your_app_password"

adapter_settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
adapter = BotFrameworkAdapter(adapter_settings)

app = web.Application()
app.router.add_post("/api/messages", handle_activity)

if __name__ == "__main__":
    web.run_app(app, host="localhost", port=3978)
