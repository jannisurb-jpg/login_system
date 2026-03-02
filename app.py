import flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, redirect, url_for, make_response, session
from datetime import datetime, timedelta
import re
import bcrypt

app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.secret_key = "SessionTestKey123"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(seconds=20)

developMode = True
minPasswordLength = 6
howManyTriesInXTime = 5
XTime = 60

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email_address = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    lastFirstTry = db.Column(db.DateTime, default=datetime.utcnow())
    triesInXTime = db.Column(db.Integer, default=0)

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        if request.form.get("GoToLogin") == "clicked":
            return redirect(url_for("login"))
        
        if request.form.get("GoTosignup") == "clicked":
            return redirect(url_for("signup"))
        

    return render_template("index.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        tried_email_address = request.form['email_address']
        tried_password = request.form['password']

        if len(tried_password) < minPasswordLength:
            return "Password too short"


        isAnEmailAddress = CheckIfEmailisAnEmail(str(tried_email_address))

        if isAnEmailAddress == True:
            new_user = User(
                email_address = tried_email_address,
                username = request.form['username'],
                password = bcrypt.hashpw(request.form['password'].encode("utf-8"), bcrypt.gensalt())
            )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))
        else:
            return "Use a proper email address"

    return render_template('Signup_Page.html')

def CheckIfEmailisAnEmail(tried_email_adress):
    print("Tried to check email")
    listOfTriedEmailElements = []
    if "@" and "." in tried_email_adress:
        listOfTriedEmailElements = re.split(r'[@.]', tried_email_adress)
        
        if len(listOfTriedEmailElements) == 3:
            return True
        else:
            return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':

        # Request password and email input
        emailOrUsername = request.form['email_address']
        password = request.form['password'].encode("utf-8")
        user = None

        user = User.query.filter_by(email_address=emailOrUsername).first()

        if user is None:
            user = User.query.filter_by(username=emailOrUsername).first()

        #check if it's the first try in a given time
        if (datetime.utcnow() - user.lastFirstTry).total_seconds() >= XTime: #check if time difference is greater or equal to max time
            user.lastFirstTry = datetime.utcnow()
            user.triesInXTime = 0

        #Check if max tries in XTIme is reached and if so give no access
        if (datetime.utcnow() - user.lastFirstTry).total_seconds() < XTime and user.triesInXTime >= howManyTriesInXTime:
            return "To many tries in a short time span"
        
        db.session.commit()


        if user and bcrypt.checkpw(password, user.password):
            print("Correct Password")
            user.triesInXTime = 0
            session["user_id"] = user.id
            session.permanent = True
            session["user_id"] = user.id

            return redirect(url_for("dashboard", username=user.username))
        else:
            user.triesInXTime += 1
            db.session.commit()
            print("Incorrect Password")
    return render_template('Login_Page.html')

@app.route('/user/<username>', methods=['GET', 'POST'])
def dashboard(username):
    #Get the logged in username
    user = User.query.filter_by(username=username).first()

    #check if session is on
    user_id = session.get("user_id")
    print("User_id: ", session.get("user_id"))

    if not user_id:
        return redirect("/login")

    if request.method == "POST":
        ChangePassword(user.id)
        DeleteAccount(request.form.get("delete"))

    print("User:", user,
          "\nUsername: ", user.username,
          "\nID: ", user.id)
    
    if(username == "admin"):
        users = User.query.all()
        return render_template('dashboard.html', username = user.username, created_at = user.created_at, users=users)
    else:
        return render_template('dashboard.html', username = user.username, created_at = user.created_at)

def ChangePassword(user_id):
    print("tried to change password")
    user = User.query.get(user_id)
    newPassword = request.form['change_password']

    user.password = newPassword

    db.session.commit()

def DeleteAccount(idToDelete):
    accountToDeleteId = idToDelete
    userToDelete = User.query.get(accountToDeleteId)

    db.session.delete(userToDelete)
    db.session.commit()





if __name__ == "__main__":
    if developMode == True:
        app.run(debug=True)
    else:
        app.run(host="0.0.0.0", port=5000, debug=True)