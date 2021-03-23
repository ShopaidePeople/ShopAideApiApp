from flask import Flask, render_template, request, session
import speech_recognition as sr
import json
import requests
#from pygame import mixer 
#from pydub import AudioSegment

from flask import Blueprint
import uuid
from flask_pymongo import PyMongo
from spacymodel import SpacyModel

app=Flask(__name__)

app.config["MONGO_URI"] = "mongodb+srv://Ashwin:preetha11319@chatbot.a0mji.mongodb.net/trial?retryWrites=true&w=majority"
mongo = PyMongo(app)

sm = SpacyModel()

app.secret_key="good"

@app.route('/')
def hello_world():
    return "HI"

@app.route('/speechToText',methods=['GET','POST'])
def speechToTextFunc():
    if request.method == 'POST':
        r = sr.Recognizer()
        #audio_data = request.json
        #text = r.recognize_google(audio_data,language="hi")
        #print(text)
        #return text
        audio_file=None
        audio_file = request.files['file']
        if(audio_file==None):
            return "Sorry"
        text="Dummy"
        with sr.AudioFile(audio_file) as source:
            # listen for the data (load audio to memory)
            audio_data = r.record(source)
            # recognize (convert from speech to text)
            text = r.recognize_google(audio_data,language="hi")
            print(text)
        return text
    elif request.method == 'GET':
        return 'get method received' 
    
    


@app.route('/textToSpeech',methods=['GET','POST'])
def textToSpeechFunc():
    url = "https://voicerss-text-to-speech.p.rapidapi.com/"

    querystring = {"key":"7513283cbcb64bf0803f5c41ad95810d","src":"Okay I will now load the results","hl":"en-in","r":"0","c":"mp3"}

    headers = {'x-rapidapi-key': "dc35a0cc76msh899ec247fe716fdp1d0585jsn841002085e3e",'x-rapidapi-host': "voicerss-text-to-speech.p.rapidapi.com"}

    response = requests.request("GET", url, headers=headers, params=querystring)
    return response
    

#getting params passed with url - a = request.args.get('user')

@app.route('/updateNerModel',methods=['GET','POST'])
def updateNerModelFunc():
    sm.tsv_to_json_format("./testing_data.tsv",'./testing_data.json','abc')
    sm.prepareTrainingData('./testing_data.json','./testing_data_out.py')
    sm.modelPreparation(None,"en_core_web_sm",'./def',10)
    return '<h1>Successfully upadted NER model</h1>'

@app.route('/getRankProducts',methods=['GET','POST'])
def getRankProductsFunc():

    unique_id = request.args.get('uid')
    sentence = request.args.get('uinput') 

    ner_output = sm.testing_func('./def',sentence)

    print(ner_output)

    unique_id_text = str(unique_id)+"text"
    inputs = mongo.db[unique_id_text]
    for keys in ner_output:
        insert_dict = {keys:ner_output[keys]} 
        inputs.insert_one(insert_dict)

    true = True
    false = False
    #To generate a unique id and create a table with that id for a user for one session
    id = uuid.uuid4()
    unique_id = str(id)

    user_collection = mongo.db[unique_id]
    print(unique_id)
    
    s = unique_id 
    
    collections = mongo.db[s]
    
    url = "https://amazon-product-reviews-keywords.p.rapidapi.com/product/search"
    querystring = {"keyword":"samsung galaxy s20","country":"US","category":"aps"}
    headers = {'x-rapidapi-key': "dc35a0cc76msh899ec247fe716fdp1d0585jsn841002085e3e",'x-rapidapi-host': "amazon-product-reviews-keywords.p.rapidapi.com"}
    response = requests.request("GET", url, headers=headers, params=querystring)
    
    amazon_dict = {}
    amazon_dict['amazon'] = json.loads(response.text)
    
    for i in amazon_dict['amazon']['products']:
        collections.insert_one(i)

    collections = mongo.db[s].find()

    for i in collections:
        if("Sponsored Ad" in i['title']):
            mongo.db[s].delete_one(i)
        if(int(i['price']['current_price'])==0):
            mongo.db[s].delete_one(i)

    collections = mongo.db[s].find()
    for i in collections:
        url = "https://amazon23.p.rapidapi.com/reviews"
        querystring = {"asin":i['asin'],"sort_by":"recent","country":"US"}
        headers = {'x-rapidapi-key': "e8b9bd5ec6msha82feacde4f4892p10370ejsn6fd0e65335d6",'x-rapidapi-host': "amazon23.p.rapidapi.com"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        results = response.json()

        filterr = { 'asin': i['asin'] } 
        newvalues = { "$set": { 'stars_stat': results['stars_stat'] } } 
        mongo.db[s].update_one(filterr, newvalues)


    max_price = -999999.0
    collections = mongo.db[s].find() 

    for i in collections:
        if(float(i['price']['current_price'])>float(max_price)):
            max_price = float(i['price']['current_price'])

    collections = mongo.db[s].find()

    for i in collections:
        users = int(i['reviews']['total_reviews'])
        star1 = (i['stars_stat']['1'])
        stars1 = (int(star1[:len(star1)-1])/100)*users
        star2 = (i['stars_stat']['2'])
        stars2 = (int(star2[:len(star2)-1])/100)*users
        star3 = (i['stars_stat']['3'])
        stars3 = (int(star3[:len(star3)-1])/100)*users
        star4 = (i['stars_stat']['4'])
        stars4 = (int(star4[:len(star4)-1])/100)*users
        star5 = (i['stars_stat']['5'])
        stars5 = (int(star5[:len(star5)-1])/100)*users
        ratings_ratio = 0.0
        if(users!=0):
            ratings_ratio += ((stars1+stars2+stars3)/(stars1+stars2+stars3+stars4+stars5))*0.225
        else:
            ratings_ratio+=1.0
        if((stars4+stars5)!=0):
            ratings_ratio += ((stars1+stars2+stars3+stars4+stars5)/(stars4+stars5))*0.225
        else:
            ratings_ratio += 1.0


        price_ratio = (float(i['price']['current_price'])/max_price)*0.35
        
        total_reviews_rate = 0.0
        total_review_number = int(i['reviews']['total_reviews'])

        if(total_review_number<=500):
            total_reviews_rate+=1
        elif(total_review_number<=1000):
            total_reviews_rate+=0.75
        elif(total_review_number<=5000):
            total_reviews_rate+=0.5
        else:
            total_reviews_rate+=0.25

        ranking_pnt = ratings_ratio + price_ratio + (total_reviews_rate*0.1)

        if("Renewed" in i['title']):
            ranking_pnt += 1.0

        print(ranking_pnt)
        filterr = {'asin':i['asin']}
        newvalues = {"$set" : {'ranking_points':ranking_pnt}}
        mongo.db[s].update_one(filterr,newvalues)

    #required --- mongo.db[unique_id].drop()
    return '<h1>Products ranked successfully</h1>'
          
if __name__ == "__main__":
    #app.debug=True
    app.run(port="5000")
