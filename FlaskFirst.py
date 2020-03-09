from flask import Flask
application = Flask(__name__)   # instanciate an instance of the Flask class

@application.route("/")
def index():
    return "Hello World !"

if __name__== "__main__":
    application.run(debug=True)

