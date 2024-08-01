import os
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity, ActivityTypes, Attachment, AttachmentLayoutTypes
from botbuilder.core.integration import aiohttp_error_middleware
from botframework.connector.auth import MicrosoftAppCredentials
from aiohttp import web
import base64
import tempfile

APP_ID = os.environ.get("MicrosoftAppId", "")
APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")

class TeamsBot:
    def __init__(self):
        self.conversation_state = {}

    async def on_turn(self, turn_context: TurnContext):
        user_id = turn_context.activity.from_property.id
        if user_id not in self.conversation_state:
            self.conversation_state[user_id] = {"state": "start", "chat_log": []}

        if turn_context.activity.type == ActivityTypes.message:
            # Log user message
            self.conversation_state[user_id]["chat_log"].append(f"User: {turn_context.activity.text}")

            text = turn_context.activity.text.lower()
            state = self.conversation_state[user_id]["state"]

            if text == "end chat":
                await self._end_chat(turn_context, user_id)
                return

            if state == "start" and text == "start":
                await self._ask_os_details(turn_context)
                self.conversation_state[user_id]["state"] = "os_details"
            elif state == "os_details":
                self.conversation_state[user_id]["os_details"] = text
                await self._ask_epo_version(turn_context)
                self.conversation_state[user_id]["state"] = "epo_version"
            elif state == "epo_version":
                self.conversation_state[user_id]["epo_version"] = text
                await self._ask_issue(turn_context)
                self.conversation_state[user_id]["state"] = "issue"
            elif state == "issue":
                if text in ["crash/hang", "communication", "tbd"]:
                    self.conversation_state[user_id]["issue"] = text
                    await self._end_conversation(turn_context)
                    self.conversation_state[user_id]["state"] = "chat_options"
                elif text == "licence":
                    self.conversation_state[user_id]["issue"] = text
                    await self._ask_licence_issue(turn_context)
                    self.conversation_state[user_id]["state"] = "licence_issue"
                else:
                    await self._invalid_option(turn_context)
                    await self._ask_issue(turn_context)
            elif state == "licence_issue":
                if text == "licence not getting activated":
                    await self._ask_license_not_activated_issue(turn_context)
                    self.conversation_state[user_id]["state"] = "license_not_activated_issue"
                elif text == "incorrect version/quantity":
                    await self._show_contact_info_pme(turn_context)
                    await self._end_conversation(turn_context)
                    self.conversation_state[user_id]["state"] = "chat_options"
                elif text == "software related query":
                    await self._software_ques_1(turn_context)
                    self.conversation_state[user_id]["state"] = "software_related_query_check"
                else:
                    await self._invalid_option(turn_context)
                    await self._ask_licence_issue(turn_context)
            elif state == "license_not_activated_issue":
                if text == "license already in use":
                    self.conversation_state[user_id]["licence_issue"] = "license already in use"
                    await self._show_contact_info_pme(turn_context)
                    await self._end_conversation(turn_context)
                    self.conversation_state[user_id]["state"] = "chat_options"
                else:
                    await self._invalid_option(turn_context)
                    await self._ask_license_not_activated_issue(turn_context)
            elif state == "software_related_query_check":
                if text == "yes":
                    await self._end_conversation(turn_context)
                    self.conversation_state[user_id]["state"] = "chat_options"
                elif text == "no":
                    await self._software_ques_2(turn_context)
                    self.conversation_state[user_id]["state"] = "software_related_query_check_2"
                else:
                    await self._invalid_option(turn_context)
                    await self._software_ques_1(turn_context)
            elif state == "software_related_query_check_2":
                if text == "yes":
                    await self._end_conversation(turn_context)
                    self.conversation_state[user_id]["state"] = "chat_options"
                elif text == "no":
                    await self._show_contact_info_global(turn_context)
                    await self._end_conversation(turn_context)
                    self.conversation_state[user_id]["state"] = "chat_options"
                else:
                    await self._invalid_option(turn_context)
                    await self._software_ques_2(turn_context, next_step=True)
            elif state == "chat_options":
                if text == "download":
                    await self._send_chat_file(turn_context, user_id)
                else:
                    await self._invalid_option(turn_context)
                    await self._show_chat_options(turn_context)
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
        reply = Activity(
            type=ActivityTypes.message,
            text="Please type your OS details.",
            suggested_actions={
                "actions": [
                    {"type": "imBack", "title": "End Chat", "value": "end chat"},
                ]
            },
        )
        await turn_context.send_activity(reply)
        self.conversation_state[turn_context.activity.from_property.id]["chat_log"].append("Bot: Please type your OS details.")

    async def _ask_epo_version(self, turn_context: TurnContext):
        reply = Activity(
            type=ActivityTypes.message,
            text="Please type your EPO version.",
            suggested_actions={
                "actions": [
                    {"type": "imBack", "title": "End Chat", "value": "end chat"},
                ]
            },
        )
        await turn_context.send_activity(reply)
        self.conversation_state[turn_context.activity.from_property.id]["chat_log"].append("Bot: Please type your EPO version.")

    async def _ask_issue(self, turn_context: TurnContext):
        reply = Activity(
            type=ActivityTypes.message,
            text="What issue are you facing?",
            suggested_actions={
                "actions": [
                    {"type": "imBack", "title": "Crash/Hang", "value": "crash/hang"},
                    {"type": "imBack", "title": "Communication", "value": "communication"},
                    {"type": "imBack", "title": "Licence", "value": "licence"},
                    {"type": "imBack", "title": "TBD", "value": "tbd"},
                    {"type": "imBack", "title": "End Chat", "value": "end chat"},
                ]
            },
        )
        await turn_context.send_activity(reply)
        self.conversation_state[turn_context.activity.from_property.id]["chat_log"].append("Bot: What issue are you facing?")

    async def _ask_licence_issue(self, turn_context: TurnContext):
        reply = Activity(
            type=ActivityTypes.message,
            text="What licence issue are you facing?",
            suggested_actions={
                "actions": [
                    {"type": "imBack", "title": "Software related query", "value": "software related query"},
                    {"type": "imBack", "title": "Licence not getting activated", "value": "licence not getting activated"},
                    {"type": "imBack", "title": "Incorrect Version/Quantity", "value": "incorrect version/quantity"},
                    {"type": "imBack", "title": "End Chat", "value": "end chat"},
                ]
            },
        )
        await turn_context.send_activity(reply)
        self.conversation_state[turn_context.activity.from_property.id]["chat_log"].append("Bot: What licence issue are you facing?")

    async def _ask_license_not_activated_issue(self, turn_context: TurnContext):
        reply = Activity(
            type=ActivityTypes.message,
            text="What issue are you facing with licence activation?",
            suggested_actions={
                "actions": [
                    {"type": "imBack", "title": "License already in use", "value": "license already in use"},
                    {"type": "imBack", "title": "End Chat", "value": "end chat"},
                ]
            },
        )
        await turn_context.send_activity(reply)
        self.conversation_state[turn_context.activity.from_property.id]["chat_log"].append("Bot: What issue are you facing with licence activation?")

    async def _show_contact_info_pme(self, turn_context: TurnContext):
        contact_message = "Please contact support at pme-ordersupport@schneider-electric.com with your ActivationID and other requirements."
        await turn_context.send_activity(contact_message)
        self.conversation_state[turn_context.activity.from_property.id]["chat_log"].append(f"Bot: {contact_message}")

    async def _software_ques_1(self, turn_context: TurnContext, next_step=False):
        contact_message = "Check for valid license and required license count is present in lecensing tool LCT/FLM."
        await turn_context.send_activity(contact_message)
        self.conversation_state[turn_context.activity.from_property.id]["chat_log"].append(f"Bot: {contact_message}")

        if not next_step:
            reply = Activity(
                type=ActivityTypes.message,
                text="Did this resolve your issue?",
                suggested_actions={
                    "actions": [
                        {"type": "imBack", "title": "Yes", "value": "yes"},
                        {"type": "imBack", "title": "No", "value": "no"},
                    ]
                },
            )
            await turn_context.send_activity(reply)
            self.conversation_state[turn_context.activity.from_property.id]["chat_log"].append("Bot: Did this resolve your issue?")

    async def _software_ques_2(self, turn_context: TurnContext, next_step=False):
        contact_message = "Collect client service/System services kernel dump from all PO machine in architecture to verify licencse acquisition."
        await turn_context.send_activity(contact_message)
        self.conversation_state[turn_context.activity.from_property.id]["chat_log"].append(f"Bot: {contact_message}")

        if not next_step:
            reply = Activity(
                type=ActivityTypes.message,
                text="Did this resolve your issue?",
                suggested_actions={
                    "actions": [
                        {"type": "imBack", "title": "Yes", "value": "yes"},
                        {"type": "imBack", "title": "No", "value": "no"},
                    ]
                },
            )
            await turn_context.send_activity(reply)
            self.conversation_state[turn_context.activity.from_property.id]["chat_log"].append("Bot: Did this resolve your issue?")

    async def _show_contact_info_global(self, turn_context: TurnContext):
        msg = "Please contact support at global-ems-tech-support@schneider-electric.com with PO Logs, Architecture, and licence machine details."
        await turn_context.send_activity(msg)
        self.conversation_state[turn_context.activity.from_property.id]["chat_log"].append(f"Bot: {msg}")

    async def _invalid_option(self, turn_context: TurnContext):
        await turn_context.send_activity("Invalid option. Please select one of the provided options.")
        self.conversation_state[turn_context.activity.from_property.id]["chat_log"].append("Bot: Invalid option. Please select one of the provided options.")

    async def _end_conversation(self, turn_context: TurnContext):
        user_id = turn_context.activity.from_property.id
        os_details = self.conversation_state[user_id].get("os_details", "Not provided")
        epo_version = self.conversation_state[user_id].get("epo_version", "Not provided")
        issue = self.conversation_state[user_id].get("issue", "Not provided")
        licence_issue = self.conversation_state[user_id].get("licence_issue", "Not provided")

        summary = f"Thank you for your responses.\nOS Details: {os_details}\nEPO Version: {epo_version}\nIssue: {issue}\nLicence Issue: {licence_issue}"
        await turn_context.send_activity(summary)
        self.conversation_state[user_id]["chat_log"].append(f"Bot: {summary}")

        await self._show_chat_options(turn_context)

    async def _show_chat_options(self, turn_context: TurnContext):
        reply = Activity(
            type=ActivityTypes.message,
            text="Would you like to download the chat log?",
            suggested_actions={
                "actions": [
                    {"type": "imBack", "title": "Download", "value": "download"},
                    {"type": "imBack", "title": "End Chat", "value": "end chat"},
                ]
            },
        )
        await turn_context.send_activity(reply)

    async def _send_chat_file(self, turn_context: TurnContext, user_id: str):
        chat_log = "\n".join(self.conversation_state[user_id]["chat_log"])
        
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as temp_file:
            temp_file.write(chat_log)
            temp_file_path = temp_file.name

        with open(temp_file_path, 'rb') as file:
            file_content = file.read()
        
        base64_content = base64.b64encode(file_content).decode()

        attachment = Attachment(
            content_type="text/plain",
            name="chat_log.txt",
            content_url=f"data:text/plain;base64,{base64_content}"
        )

        reply = Activity(
            type=ActivityTypes.message,
            attachments=[attachment],
            attachment_layout=AttachmentLayoutTypes.list
        )

        await turn_context.send_activity(reply)
        await turn_context.send_activity("Chat log file has been sent. You can download it from the attachment.")
        
        os.unlink(temp_file_path)  # Delete the temporary file

        await self._show_chat_options(turn_context)

    async def _end_chat(self, turn_context: TurnContext, user_id: str):
        await turn_context.send_activity("Chat has been ended. Click 'Start' to begin a new chat.")
        self.conversation_state[user_id] = {"state": "start", "chat_log": []}
        await self._show_start_button(turn_context)

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
