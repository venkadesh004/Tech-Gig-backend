from flask import Flask, request
import pyrebase
from flask_cors import CORS
import joblib
from tensorflow.keras.models import model_from_json
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pandas as pd
from sklearn.model_selection import train_test_split
# import os

# os.system("/opt/render/project/src/.venv/bin/python -m pip install --upgrade pip")

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = "faslkdfjlaskdfjl;sdkfj"

firebaseConfig = {
  "apiKey": "AIzaSyALzbrFOUwOMNuYFtFqrbs3UlXbQveUbpE",
  "authDomain": "intel-hackathon-69537.firebaseapp.com",
  "databaseURL": "https://intel-hackathon-69537-default-rtdb.asia-southeast1.firebasedatabase.app",
  "projectId": "intel-hackathon-69537",
  "storageBucket": "intel-hackathon-69537.appspot.com",
  "messagingSenderId": "370106770915",
  "appId": "1:370106770915:web:71cb05c5fe16effd296cd6",
  "measurementId": "G-Q0P4FVT0Y8"
}

data = pd.read_csv('review.csv')

X_train, X_test, y_train, y_test = train_test_split(data['review'], data['sentiment'], test_size=0.001)

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

json_file = open('model.json', 'r')
loaded_model_json = json_file.read()
json_file.close()
loaded_model = model_from_json(loaded_model_json)

loaded_model.load_weights("model.h5")

tokenizer = Tokenizer(num_words=10000, oov_token='<OOV>')
tokenizer.fit_on_texts(X_train)

@app.route('/<string:username>', methods=["GET", "POST"])
def getUser(username):
    if request.method == "POST":
        password = request.get_json()["password"]
        users = db.child("users").get().val()

        print(users)

        if users == None:
            return "No Data"
        
        for i in users:
            # print(users[i])
            if users[i]["username"] == username:
                if users[i]["password"] == password:
                    return "Correct password"
                else:
                    return "Wrong password"

    return "Not Found"

@app.route('/addUser', methods=["POST"])
def addUser():
    if request.method == "POST":
        data = request.get_json()

        # print(data)

        users = db.child("users").get().val()
        # print(users)

        if users != None:
            for i in users:
                if users[i]["username"] == data["username"]:
                    return "Already username exsists"
                elif users[i]["email"] == data["email"]:
                    return "Already Email exsists"

        db.child("users").push(data)

        return "Done"
    
    return "Error"

@app.route('/getItems', methods=["GET"])
def getItems():
    items = db.child("products").get().val()

    if items == None:
        return "No Items"
    
    l = []

    for i in items:
        l.append(items[i])

    return l

@app.route('/getItem/<string:itemID>', methods=["GET"])
def getItem(itemID):
    items = db.child("products").get().val()

    for i in items:
        if items[i]["itemID"] == int(itemID):
            comments = items[i]["comments"]

            classify = []

            for j in comments:
                user_review = j

                user_review = tokenizer.texts_to_sequences([user_review])
                user_review = pad_sequences(user_review, maxlen=100, padding='post', truncating='post')

                # Predict sentiment for user review
                sentiment = loaded_model.predict(user_review)

                # Print the predicted sentiment
                # print(sentiment)
                if sentiment > 0.6:
                    classify.append(1)
                elif sentiment < 0.6 and sentiment >= 0.1:
                    classify.append(0)
                else:
                    classify.append(-1)

            items[i]["classify"] = classify

            return items[i]

    # print(items)

    return "NOT FOUND"

@app.route('/addItems', methods=["POST"])
def addItem():
    if request.method == "POST":
        data = request.get_json()

        print(data)

        admins = db.child("admins").get().val()
        print('Admin', admins)

        itemID = db.child("itemCount").get().val()
        data["itemID"] = itemID+1

        l = []

        for i in admins:
            print(admins[i])
            print(admins[i]["username"], admins[i]["products"])
            if admins[i]["username"] == data["adminUsername"]:
                if (admins[i]["products"] == ""):
                    l = []
                else:
                    l = admins[i]["products"]
                break

        l.append(itemID+1)

        db.child("admins").child(i).update({"products": l})

        db.update({"itemCount": itemID+1})

        db.child("products").push(data)

        return "Done"
    
    return "Error"

@app.route('/deleteItems', methods=["GET", "POST"])
def deleteItem():
    if request.method == "POST":
        data = request.get_json()

        print(data)

        items = db.child("products").get().val()

        for i in items:
            if items[i]["itemID"] == data["itemID"]:
                if items[i]["adminUsername"] == data["username"]:
                    db.child("products").child(i).remove()
                    db.update({"itemCount": db.child("itemCount").get().val()-1})
                    return "Done"
        
        return "Not Found"
    
    return "Error"


@app.route('/addComments/<string:itemID>', methods=["GET", "POST"])
def addComments(itemID):
    if request.method == "POST":
        data = request.get_json()

        items = db.child("products").get().val()
        users = db.child("users").get().val()

        # print(items)

        if items != None and users != None:
            l = []
            l2 = []
            l3 = []

            for i in items:
                if items[i]["itemID"] == int(itemID):
                    l = db.child("products").child(i).child("comments").get().val()
                    l2 = db.child("products").child(i).child("comment-users").get().val()

                    if l == "":
                        l = []

                    if l2 == "":
                        l2 = []

                    break

            for j in users:
                if users[j]["email"] == data["user-email"]:
                    l3 = db.child("users").child(j).child("comments").get().val()
                    if l3 == "":
                        l3 = []

                    break

            l.append(data["comments"])
            l2.append(data["user-email"])
            l3.append(itemID)

            db.child("products").child(i).update({"comments": l})
            db.child("products").child(i).update({"comment-users": l2})
            db.child("users").child(j).update({"comments": l3})

            return "Done"

    return "Error"

@app.route('/addToCart/<string:itemID>', methods=["GET", "POST"])
def addToCart(itemID):
    if request.method == "POST":
        data = request.get_json()

        items = db.child("products").get().val()
        users = db.child("users").get().val()

        if items != None and users != None:
            l = []
            l3 = []

            for i in items:
                if items[i]["itemID"] == int(itemID):
                    l = db.child("products").child(i).child("brought").get().val()

                    if l == "":
                        l = []

                    break

            for j in users:
                if users[j]["email"] == data["user-email"]:
                    l3 = db.child("users").child(j).child("products").get().val()
                    if l3 == "":
                        l3 = []

                    break

            l.append(data["user-email"])
            l3.append(itemID)

            db.child("products").child(i).update({"brought": l})
            db.child("users").child(j).update({"products": l3})

            return "Done"

    return "Error"

@app.route('/removeFromCart/<string:itemID>', methods=["GET", "POST"])
def removeFromCart(itemID):
    if request.method == "POST":
        user = request.get_json()

        items = db.child("products").get().val()
        users = db.child("users").get().val()

        if items != None and users != None:
            l = []
            l2 = []

            for i in items:
                if items[i]["itemID"] == int(itemID):
                    l = db.child("products").child(i).child("brought").get().val()

                    if l == "":
                        return "Error"
                    
            for j in users:
                if items[i]["itemID"] == int(itemID):
                    l2 = db.child("users").child(i).child("products").get().val()

                    if l2 == "":
                        return "Error"
                    
            for k in range(len(l)):
                if l[k] == user["user-email"]:
                    l.pop(k)

            for k in range(len(l2)):
                if str(l[k]) == str(itemID):
                    l.pop(k)

            db.child("products").child(i).update({"brought": l})
            db.child("users").child(j).update({"products": l2})

            return "Done"
        
    
    return "Error"

@app.route('/addAdmin', methods=["POST"])
def addAdmin():
    if request.method == "POST":
        data = request.get_json()

        # print(data)

        users = db.child("admins").get().val()
        # print(users)

        if users != None:
            for i in users:
                if users[i]["username"] == data["username"]:
                    return "Already username exsists"
                elif users[i]["email"] == data["email"]:
                    return "Already Email exsists"

        db.child("admins").push(data)

        return "Done"
    
    return "Error"

@app.route('/admin/login/<string:username>', methods=["GET", "POST"])
def getAdmin(username):
    if request.method == "POST":
        password = request.get_json()["password"]
        users = db.child("admins").get().val()

        print(users)

        if users == None:
            return "No Data"
        
        for i in users:
            # print(users[i])
            if users[i]["username"] == username:
                if users[i]["password"] == password:
                    return "Correct password"
                else:
                    return "Wrong password"

    return "Not Found"

@app.route('/admin/<string:username>/getItems', methods=["GET"])
def adminGetItems(username):
    admins = db.child("admins").get().val()
    
    l = []
    for i in admins:
        if admins[i]["username"] == username:
            if admins[i]["products"] != "":
                l = admins[i]["products"]
    
    items = db.child("products").get().val()

    output = []

    if l != []:
        for i in items:
            for j in l:
                if items[i]["itemID"] == j:
                    classify = []

                    for j in items[i]["comments"]:
                        user_review = j

                        user_review = tokenizer.texts_to_sequences([user_review])
                        user_review = pad_sequences(user_review, maxlen=100, padding='post', truncating='post')

                        # Predict sentiment for user review
                        sentiment = loaded_model.predict(user_review)

                        # Print the predicted sentiment
                        # print(sentiment)
                        if sentiment > 0.6:
                            classify.append(1)
                        elif sentiment < 0.6 and sentiment >= 0.1:
                            classify.append(0)
                        else:
                            classify.append(-1)

                    items[i]["classify"] = classify
                    output.append(items[i])
        return output
    else:
        return "Empty Product Menu"

    return "Error"

if __name__ == "__main__":
    app.run(debug=True)