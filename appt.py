import os
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity, ActivityTypes
from botbuilder.core.integration import aiohttp_error_middleware
from botframework.connector.auth import MicrosoftAppCredentials
from aiohttp import web

# Use environment variables for App ID and Password
APP_ID = os.environ.get("MicrosoftAppId", "")
APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

class TeamsBot:
    async def on_turn(self, turn_context: TurnContext):
        if turn_context.activity.type == ActivityTypes.message:
            text = turn_context.activity.text.lower()

            if text == "hi":
                await self._ask_question1(turn_context)
            elif text in ["option1", "option2"]:
                await self._ask_question2(turn_context)
            elif text in ["option3", "option4"]:
                await self._end_conversation(turn_context)
            else:
                await turn_context.send_activity("Please say 'hi' to start.")

    async def _ask_question1(self, turn_context: TurnContext):
        reply = Activity(
            type=ActivityTypes.message,
            text="Question 1: Choose an option",
            suggested_actions={
                "actions": [
                    {"type": "imBack", "title": "Option 1", "value": "option1"},
                    {"type": "imBack", "title": "Option 2", "value": "option2"},
                ]
            },
        )
        await turn_context.send_activity(reply)

    async def _ask_question2(self, turn_context: TurnContext):
        reply = Activity(
            type=ActivityTypes.message,
            text="Question 2: Choose another option",
            suggested_actions={
                "actions": [
                    {"type": "imBack", "title": "Option 3", "value": "option3"},
                    {"type": "imBack", "title": "Option 4", "value": "option4"},
                ]
            },
        )
        await turn_context.send_activity(reply)

    async def _end_conversation(self, turn_context: TurnContext):
        await turn_context.send_activity("Thank you for your responses. Say 'hi' to start again.")

bot = TeamsBot()

# Create BotFrameworkAdapterSettings
settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)

# Initialize the adapter with the settings
adapter = BotFrameworkAdapter(settings)

async def messages(req: web.Request) -> web.Response:
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

    async def call_bot(turn_context):
        await bot.on_turn(turn_context)

    try:
        await adapter.process_activity(activity, auth_header, call_bot)
        return web.Response(status=200)
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise web.HTTPBadRequest()

app = web.Application(middlewares=[aiohttp_error_middleware])
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    web.run_app(app, host="localhost", port=3978)
