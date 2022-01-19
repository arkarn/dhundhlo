from flask import Flask, request, json, redirect, url_for, send_file, session
from flask import render_template
import pgeocode
nomi = pgeocode.Nominatim('in')

  
app = Flask(__name__)
app.debug = True

import pymongo
myclient = pymongo.MongoClient("mongodb+srv://arkiitkgp:admin123@cluster0.a8wtp.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
coll = myclient["dhundhlo"]["jobs"]

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/done", methods=['POST'])
def done():
    if 'experience' in request.form.keys():
        experience = request.form["experience"]
    else:
        experience = 1
    jobdict = {"jobrole": request.form["role"], 
              "company": request.form["company"], 
              "experience": experience, 
              "address": request.form["address"], 
              "pincode": request.form["pin"], 
              "city": request.form["city"],  
              "phone": request.form["phone"]}
    details = nomi.query_postal_code(request.form['pin'])
    jobdict["latlon"] = [details['latitude'], details['longitude']]
    coll.insert_one(jobdict)
    return render_template('thankyou.html')

    
if __name__ == '__main__':
   app.run(host='0.0.0.0', port=80, debug=True)


