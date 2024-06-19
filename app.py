# from flask import Flask, render_template, request, jsonify

# app = Flask(__name__)

# @app.route("/")
# def home():
#     return render_template("index.html")

# @app.route("/get")
# def get_bot_response():
#     user_input = request.args.get('msg')
#     response, end_conversation = chat_logic(user_input)
#     return jsonify(response=response, end_conversation=end_conversation)

# def chat_logic(user_input):
#     # Initial options
#     if user_input.lower() in ["start", "hi", "hello"]:
#         return "Choose an option:\nA: Option A\nB: Option B", False

#     # Handling the first choice
#     if user_input.lower() == "a":
#         return "You chose A. Now choose:\nC: Option C\nD: Option D", False
#     elif user_input.lower() == "b":
#         return "You chose B. Now choose:\nE: Option E\nF: Option F", False

#     # Handling the second choice for path A
#     if user_input.lower() == "c":
#         return "You chose C. Here is your final response for path A -> C. Bye!", True
#     elif user_input.lower() == "d":
#         return "You chose D. Here is your final response for path A -> D. Bye!", True

#     # Handling the second choice for path B
#     if user_input.lower() == "e":
#         return "You chose E. Here is your final response for path B -> E. Bye!", True
#     elif user_input.lower() == "f":
#         return "You chose F. Here is your final response for path B -> F. Bye!", True

#     return "Invalid choice. Please start by typing 'start', 'hi', or 'hello'.", False

# if __name__ == "__main__":
#     app.run()
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get")
def get_bot_response():
    user_input = request.args.get('msg')
    response, end_conversation = chat_logic(user_input)
    return jsonify(response=response, end_conversation=end_conversation)

def chat_logic(user_input):
    if not hasattr(chat_logic, "step"):
        chat_logic.step = 0

    if chat_logic.step == 0:
        chat_logic.step += 1
        return "Please provide your OS details:", False
    
    if chat_logic.step == 1:
        chat_logic.os_details = user_input
        chat_logic.step += 1
        return "Please provide your driver version:", False

    if chat_logic.step == 2:
        chat_logic.driver_version = user_input
        chat_logic.step += 1
        return f"OS details: {chat_logic.os_details}, Driver version: {chat_logic.driver_version}. Choose an option:\nA: Option A\nB: Option B", False

    if chat_logic.step == 3 and user_input.lower() == "a":
        chat_logic.step += 1
        return "You chose A. Now choose:\nC: Option C\nD: Option D", False
    elif chat_logic.step == 3 and user_input.lower() == "b":
        chat_logic.step += 1
        return "You chose B. Now choose:\nE: Option E\nF: Option F", False

    if chat_logic.step == 4:
        if user_input.lower() == "c":
            return "You chose C. Here is your final response for path A -> C. Bye!", True
        elif user_input.lower() == "d":
            return "You chose D. Here is your final response for path A -> D. Bye!", True
        elif user_input.lower() == "e":
            return "You chose E. Here is your final response for path B -> E. Bye!", True
        elif user_input.lower() == "f":
            return "You chose F. Here is your final response for path B -> F. Bye!", True

    return "Invalid input. Please start by typing 'start', 'hi', or 'hello'.", False

if __name__ == "__main__":
    app.run()
