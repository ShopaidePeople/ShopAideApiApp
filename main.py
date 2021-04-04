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

import json
import random

app=Flask(__name__)

app.config["MONGO_URI"] = "mongodb+srv://Ashwin:preetha11319@chatbot.a0mji.mongodb.net/trial?retryWrites=true&w=majority"
mongo = PyMongo(app)

sm = SpacyModel()

app.secret_key="good"

@app.route('/')
def hello_world():
    return "HI"

@app.route('/welcome')
def welcome():
    id = uuid.uuid4()
    unique_id = str(id)
    return unique_id

@app.route('/speechToText',methods=['POST'])
def speechToTextFunc():
    
    text="hello"
    r = sr.Recognizer()
    audio_file=None
    audio_file = request.files['file']
    print(request.files['file'], " ", audio_file)
    print("file recieved".format(audio_file))
    if(audio_file==None):
        return flask.jsonify({"result":"Sorry"})
    text="Dummy"
    with sr.AudioFile(audio_file) as source:
        # listen for the data (load audio to memory)
            audio_data = r.record(source)
            # recognize (convert from speech to text)
            text = r.recognize_google(audio_data,language="en-IN")
    print(text)
    return text
    
    


@app.route('/textToSpeech',methods=['GET','POST'])
def textToSpeechFunc():
    url = "https://voicerss-text-to-speech.p.rapidapi.com/"

    querystring = {"key":"7513283cbcb64bf0803f5c41ad95810d","src":"Okay I will now load the results","hl":"en-in","r":"0","c":"mp3"}

    headers = {'x-rapidapi-key': "dc35a0cc76msh899ec247fe716fdp1d0585jsn841002085e3e",'x-rapidapi-host': "voicerss-text-to-speech.p.rapidapi.com"}

    response = requests.request("GET", url, headers=headers, params=querystring)
    return response
    

#getting params passed with url - a = request.args.get('user')

@app.route('/getBotReply',methods=['GET','POST'])
def chatbot():
    uid = request.args.get('uid')
    msg = request.args.get('msg')
    print(msg)
    msg = str(msg)
    if(msg[0]=="\""):
       msg = msg[1:]
    if(msg[len(msg)-1]=="\""):
        msg = msg[:len(msg)-1]
    uid = str(uid)+'chat'
    f = open('./voicebotData.json',)
    data = json.load(f)
    result_text = ""
    for i in data['reply']:
        if(i["mesg"].lower().strip()==msg.lower().strip()):
            lgth = len(i["answer"])
            rnd = random.randint(0,lgth-1)
            result_text = i["answer"][rnd] 
            break
    for i in data['reply']:
        if((msg.lower().strip() in i["mesg"].lower().strip())):
            lgth = len(i["answer"])
            rnd = random.randint(0,lgth)
            result_text = i["answer"][rnd]
            break
    if(result_text==""):
        result_text = "Sorry. I can't understand. "
    
    print(uid)
    user_collection = mongo.db[uid]
    
    collections = mongo.db[uid]
    collections.insert_one({"user":msg})
    collections.insert_one({"bot":result_text})
    f.close()
    print("===========================================================================")

    return result_text



@app.route('/featureIdentification',methods=['GET','POST'])
def featureIdentificationFunction():


    uid = request.args.get('uid')
    collections  = mongo.db[(str(uid)+'chat')].find()
    uid = str(uid)+'features'


    user_collection = mongo.db[uid]
    
    result_ner = {}
    for i in collections:
        if("user" in  i):
            ner_output = sm.testing_func('./def',i["user"])
            for val in ner_output:
                print("val is " , val)
                if(val=='_id'):
                    continue
                result_ner[val] = ner_output[val]
            print("ner output is" ,ner_output)
    
    user_collection.insert_one(result_ner)
    del result_ner['_id']
    print("result ner is",result_ner)
    return (result_ner)


@app.route('/getProducts')
def getProductsFunction():
    uid = request.args.get('uid')
    features_collection = mongo.db[str(uid)+'features']

    uid = str(uid)+'products'
    
    f = open('./productData.json',)
    data = json.load(f)

    result_data = {}
    index_var = 0

    for i in data['products']:
        present_feature = 0
        absent_feature = 0
        features_count =0 
        for val in features_collection:
            features_count+=1
            key_in_val = val.keys()[0]
            if(i[key_in_val]==val[key_in_val]):
                present_feature+=1
            else:
                absent_feature+=1
            if(absent_feature>0):
                break
        if(present_feature == features_count):
            result_data[index_var] = val
            index_var+=1

    collections = mongo.db[uid]
    collections.insert_one(result_data)

    
    f.close()
    return "Done"



@app.route('/updateNerModel',methods=['GET','POST'])
def updateNerModelFunc():
    sm.tsv_to_json_format("./testing_data.tsv",'./testing_data.json','abc')
    sm.prepareTrainingData('./testing_data.json','./testing_data_out.py')
    sm.modelPreparation(None,"en_core_web_sm",'./def',10)
    return '<h1>Successfully upadted NER model</h1>'


@app.route('/getRankProducts',methods=['GET','POST'])
def getRankProductsFunc():

    uid = request.args.get('uid')
    uid = str(uid)+'products'

    max_price = -999999
    max_deliveryFee = -999999
    collections = mongo.db[uid].find() 

    for i in collections:
        for val in i:
            if(int(val['price'])>int(max_price)):
                max_price = int(val['price'])
            if(int(val['deliveryFee']>int(max_deliveryFee))):
                max_deliveryFee = int(val['deliveryFee'])

    collections = mongo.db[uid].find()

    for i in collections:
        for val in i:
            users = int(val['totalNoofRating'])
            if(val['company']=='amazon'):
                star1 = int(val['1star'])
                stars1 = (int(star1)/100)*users
                star2 = int(val['2star'])
                stars2 = (int(star2)/100)*users
                star3 = int(val['3star'])
                stars3 = (int(star3)/100)*users
                star4 = int(val['4star'])
                stars4 = (int(star4)/100)*users
                star5 = int(val['5star'])
                stars5 = (int(star5)/100)*users
                ratings_ratio = 0.0
            else:
                stars1 = int(val['1star'])
                stars2 = int(val['2star'])
                stars3 = int(val['3star'])
                stars4 = int(val['4star'])
                stars5 = int(val['5star'])
                ratings_ratio =0.0
                
            if(users!=0):
                ratings_ratio+= ((stars1+stars2+stars3)/(stars1+stars2+stars3+stars4+stars5))*0.175
                ratings_ratio += ((stars1+stars2+stars3+stars4+stars5)/(stars4+stars5))*0.175
            else:
                ratings_ratio+=1.0
                ratings_ratio += 1.0


            price_ratio = (int(val['price'])/max_price)*0.25
            
            total_reviews_rate = 0.0
            total_review_number = int(val['totalNoofRating'])

            if(total_review_number<=500):
                total_reviews_rate+=1
            elif(total_review_number<=1000):
                total_reviews_rate+=0.75
            elif(total_review_number<=5000):
                total_reviews_rate+=0.5
            else:
                total_reviews_rate+=0.25

            deliveryTimeRatings = 0
            if(val['deliveryTime']<=1):
                deliveryTimeRatings += 0.25
            elif(val['deliveryTime']<=3):
                deliveryTimeRatings += 0.5
            elif(val['deliveryTime']<=7):
                deliveryTimeRatings += 0.75
            else:
                deliveryTimeRatings += 1.0
            

            deliveryFeeRatings = int(val['deliveryFee'])/max_deliveryFee*100

            replacementRatings = 0
            if(val['replacement']=="true"):
                replacementRatings+=0.5
            else:
                replacementRatings+=1.0

            ranking_pnt = ratings_ratio + price_ratio + (total_reviews_rate*0.1) + (deliveryTimeRatings*0.1) + (deliveryFeeRatings*0.1) +(replacementRatings*0.1)


            print(ranking_pnt)
            #filterr = {'asin':i['asin']}
            newvalues = {"$set" : {'ranking_points':ranking_pnt}}
            mongo.db[s].update_one(val,newvalues)

    #required --- mongo.db[unique_id].drop()
    return '<h1>Products ranked successfully</h1>'

if __name__ == "__main__":
    #app.debug=True
    app.run(port="5000")
