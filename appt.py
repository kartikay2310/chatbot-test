import os
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity, ActivityTypes
from botbuilder.core.integration import aiohttp_error_middleware
from botframework.connector.auth import MicrosoftAppCredentials
from aiohttp import web

APP_ID = os.environ.get("MicrosoftAppId", "")
APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

class TeamsBot:
    def __init__(self):
        self.conversation_state = {}

    async def on_turn(self, turn_context: TurnContext):
        user_id = turn_context.activity.from_property.id
        if user_id not in self.conversation_state:
            self.conversation_state[user_id] = {"state": "start"}

        if turn_context.activity.type == ActivityTypes.message:
            text = turn_context.activity.text.lower()
            state = self.conversation_state[user_id]["state"]

            if state == "start" and text == "start":
                await self._ask_os_details(turn_context)
                self.conversation_state[user_id]["state"] = "os_details"
            elif state == "os_details":
                self.conversation_state[user_id]["os_details"] = text
                await self._ask_epo_version(turn_context)
                self.conversation_state[user_id]["state"] = "epo_version"
            elif state == "epo_version":
                self.conversation_state[user_id]["epo_version"] = text
                await self._ask_question1(turn_context)
                self.conversation_state[user_id]["state"] = "question1"
            elif state == "question1":
                if text in ["option1", "option2"]:
                    await self._ask_question2(turn_context)
                    self.conversation_state[user_id]["state"] = "question2"
                else:
                    await self._invalid_option(turn_context)
                    await self._ask_question1(turn_context)
            elif state == "question2":
                if text in ["option3", "option4"]:
                    await self._end_conversation(turn_context)
                    self.conversation_state[user_id]["state"] = "start"
                else:
                    await self._invalid_option(turn_context)
                    await self._ask_question2(turn_context)
            else:
                await self._show_start_button(turn_context)
        elif turn_context.activity.type == ActivityTypes.conversation_update:
            await self._show_start_button(turn_context)

    async def _show_start_button(self, turn_context: TurnContext):
        reply = Activity(
            type=ActivityTypes.message,
            text="Welcome! Click the Start button to begin.",
            suggested_actions={
                "actions": [
                    {"type": "imBack", "title": "Start", "value": "start"},
                ]
            },
        )
        await turn_context.send_activity(reply)

    async def _ask_os_details(self, turn_context: TurnContext):
        await turn_context.send_activity("Please type your OS details.")

    async def _ask_epo_version(self, turn_context: TurnContext):
        await turn_context.send_activity("Please type your EPO version.")

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

    async def _invalid_option(self, turn_context: TurnContext):
        await turn_context.send_activity("Invalid option. Please select one of the provided options.")

    async def _end_conversation(self, turn_context: TurnContext):
        user_id = turn_context.activity.from_property.id
        os_details = self.conversation_state[user_id].get("os_details", "Not provided")
        epo_version = self.conversation_state[user_id].get("epo_version", "Not provided")
        
        summary = f"Thank you for your responses.\nOS Details: {os_details}\nEPO Version: {epo_version}\nSay 'start' to begin again."
        await turn_context.send_activity(summary)

bot = TeamsBot()

settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
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
