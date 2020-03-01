from flask import Flask
app = Flask(__name__)   # instanciate an instance of the Flask class

@app.route("/")
def index():
    return "Hello World !"

if __name__== "__main__":
    app.run(debug=True)

