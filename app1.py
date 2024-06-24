from flask import Flask, render_template, request, jsonify, session
from flask_session import Session

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

@app.route("/")
def home():
    # Clear the session data to reset the conversation
    session.clear()
    return render_template("index.html")

@app.route("/get", methods=["GET"])
def get_bot_response():
    user_input = request.args.get('msg')
    response, end_conversation, buttons = chat_logic(user_input)
    return jsonify(response=response, end_conversation=end_conversation, buttons=buttons)

def chat_logic(user_input):
    if 'step' not in session:
        session['step'] = 0

    step = session['step']

    if user_input.lower() in ["start", "hi", "hello"] and step == 0:
        session['step'] = 1
        return "Please provide your OS details:", False, []

    if step == 1:
        session['os_details'] = user_input
        session['step'] = 2
        return "Please provide your driver version:", False, []

    if step == 2:
        session['driver_version'] = user_input

        # Save the OS details and driver version to a text file
        with open("user_details.txt", "w") as file:
            file.write(f"OS details: {session['os_details']}\n")
            file.write(f"Driver version: {session['driver_version']}\n")

        session['step'] = 3
        return "Choose an option:", False, ["A: Option A", "B: Option B"]

    if step == 3:
        if user_input.lower() == "a":
            session['step'] = 4
            return "You chose A. Now choose:", False, ["C: Option C", "D: Option D"]
        elif user_input.lower() == "b":
            session['step'] = 4
            return "You chose B. Now choose:", False, ["E: Option E", "F: Option F"]

    if step == 4:
        if user_input.lower() == "c":
            return "You chose C. Here is your final response for path A -> C. Bye!", True, []
        elif user_input.lower() == "d":
            return "You chose D. Here is your final response for path A -> D. Bye!", True, []
        elif user_input.lower() == "e":
            return "You chose E. Here is your final response for path B -> E. Bye!", True, []
        elif user_input.lower() == "f":
            return "You chose F. Here is your final response for path B -> F. Bye!", True, []

    return "Invalid input. Please start by typing 'start', 'hi', or 'hello'.", False, []

if __name__ == "__main__":
    app.run(debug=True)
