
#libraries
import tweepy
import os
from textblob import TextBlob
from wordcloud import WordCloud
import pandas as pd
import math
import numpy as np
import requests
from datetime import datetime
from time import time
from numpy.core.arrayprint import str_format
import re
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
import io
import matplotlib.pyplot as plt
from google.colab import files
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import tensorflow as tf
from tensorflow import keras
from keras.layers import Bidirectional, Dropout, Activation, Dense, LSTM
from tensorflow.python.keras.layers import CuDNNLSTM
from cryptocmd import CmcScraper
from dotenv import load_dotenv




plt.style.use('fivethirtyeight')

from bs4 import BeautifulSoup 
import time
def bs4_realtimeprice(coin):
  url = "https://www.google.com/search?q=" + coin + "+price"
  HTML = requests.get(url) 
  #Parse the HTML
  soup = BeautifulSoup(HTML.text, 'html.parser') 
  text = soup.find("div", attrs={'class':'BNeawe iBp4i AP7Wnd'}).find("div", attrs={'class':'BNeawe iBp4i AP7Wnd'}).text
  return text
load_dotenv()
#Twitter API credentials
consumerKey = os.getenv("CONSUMERKEY")
consumerSecret = os.getenv("CONSUMERSECRET")
accessToken = os.getenv("ACCESSTOKEN")
accessTokenSecret = os.getenv("ACCESSTOKENSECRET")

#Create the authentication object
authenticate = tweepy.OAuthHandler(consumerKey,consumerSecret)


#set the access token and access token secret

authenticate.set_access_token(accessToken, accessTokenSecret)

#create API object while passing in the auth info
api = tweepy.API(authenticate, wait_on_rate_limit = True)

# Extract tweets from bitcoin search query
# "since" parameter exists
#replace so we do not need to hard code
day = 24
month = 5
posts_total = []

for x in range(8):
  if day < 31:
    posts = api.search(q = "bitcoin", count = 100, lang = "en", result_type = 'mixed', since = "2022-0" + str(month) +"-" + str(day), until = "2022-0" + str(month) +"-" + str(day+1), tweet_mode = 'extended')
    for tweet in posts[0:70]:
      since_date =  "2022-0"+ str(month) +"-" + str(day)
      posts_total.append([since_date.split(" ")[0], tweet.full_text])
    day += 1
  elif day == 31:
    print("correct")
    posts = api.search(q = "bitcoin", count = 100, lang = "en", result_type = 'mixed', since = "2022-0" + str(month) +"-" + str(day), until = "2022-0" + str(month+1) +"-" + str(1), tweet_mode = 'extended')
    for tweet in posts[0:70]:
      since_date =  "2022-0"+ str(month) +"-" + str(day)
      posts_total.append([since_date.split(" ")[0], tweet.full_text])
    day = 1
    month += 1  
  else:
    day = 1
    month += 1
    posts = api.search(q = "bitcoin", count = 100, lang = "en", result_type = 'mixed', since = "2022-0" + str(month) +"-" + str(day), until = "2022-0" + str(month) +"-" + str(day+1), tweet_mode = 'extended')
    for tweet in posts[0:70]:
      since_date =  "2022-0"+ str(month) +"-" + str(day)
      posts_total.append([since_date.split(" ")[0], tweet.full_text])
    day+=1


df = pd.DataFrame(posts_total)
df.columns = ['Date','Tweet']



#Show first 8 rows of data
df.head(8)

#Cleansing tweets function
def data_Cleaning(tweets):
  tweets = re.sub(r'@[A-Za-z0-9]', '', tweets) #removing mentions
  tweets = re.sub(r'#', '', tweets)
  tweets = re.sub(r'https?:\/\/\S+', '', tweets)
  tweets = re.sub(r"RT[\s]", '', tweets)
  tweets = re.sub(r"Retweet[\s]", '', tweets)
  tweets = re.sub(r"Follow[\s]", '', tweets)
  tweets = re.sub(u"\U0001F600-\U0001F64F", '', tweets) #default emotes/emojis
  tweets = re.sub(u"\U0001F300-\U0001F5FF", '', tweets) #default symbols/pictographs
  tweets = re.sub(u"\U0001F680-\U0001F6FF", '', tweets) #transportation symbols
  tweets = re.sub(u"\U0001F1E0-\U0001F1FF", '', tweets) #flags (ios)
  
  return tweets
def emoji_Cleaning(tweets):
  emoji_pattern = re.compile(
      "["
      u"\U0001F600-\U0001F64F"
      u"\U0001F300-\U0001F5FF"
      u"\U0001F680-\U0001F6FF" 
      u"\U0001F680-\U0001F6FF"   
      u"\U0001F1E0-\U0001F1FF"
      "]+",
      flags=re.UNICODE,  
  )
  return emoji_pattern.sub(r"", tweets)
#clean & print the text
df['Tweet'] = df['Tweet'].apply(data_Cleaning)
df['Tweet'] = df['Tweet'].apply(emoji_Cleaning)

df

analyzer = SentimentIntensityAnalyzer()
df['neg'] = df['Tweet'].apply(lambda x:analyzer.polarity_scores(x)['neg'])
df['neu'] = df['Tweet'].apply(lambda x:analyzer.polarity_scores(x)['neu'])
df['pos'] = df['Tweet'].apply(lambda x:analyzer.polarity_scores(x)['pos'])
df['compound'] = df['Tweet'].apply(lambda x:analyzer.polarity_scores(x)['compound'])

#show data
df

#Average Compound Values
Start_Date = df.iloc[0,0]
count = 0
Sum = 0
Compound_Averages = []
Dataset_Dates = []
Dataset_Dates.append(Start_Date)
for index, row in df.iterrows():
    if(row['Date'] == Start_Date):
      Sum+= float(row['compound'])
      count+=1
    else:
      Compound_Averages.append((Sum/count))
      Start_Date = row['Date']
      Dataset_Dates.append(Start_Date)
      Sum = 0
      count = 0
#Create Data Frame for final Values to Be Appended
Compound_Averages.append((Sum/count))
Dataset = pd.DataFrame(Dataset_Dates)
Dataset['Polarity'] = Compound_Averages
Dataset.columns = ['Date','Polarity']
Dataset

#Get bitcoin prices - Delta Price, Open, Close, High, Low

arr = []
for date in Dataset_Dates:
  tempDate = str(date)
  date = tempDate
  date = date.replace('2022-', '')
  date += '-2022'
  mid = date[0:3]
  date = date[3:]
  index = date.find('-')
  beg = date[0:index+1]
  end = date[index+1:]
  date = beg + mid+ end
  arr.append(date)
scraper = CmcScraper("BTC", arr[0], arr[7])
# Pandas dataFrame for the same data
tempPrices = scraper.get_dataframe()
tempPrices = tempPrices.iloc[::-1]
Dataset["Open"] = tempPrices["Open"]
Dataset["High"] = tempPrices["High"]
Dataset["Low"] = tempPrices["Low"]
Dataset["Volume"] = tempPrices["Volume"]
Dataset["Market Cap"] = tempPrices["Market Cap"]


Dataset["Close"] = tempPrices["Close"]

Dataset

model_dataframe = Dataset.iloc[:,1:]
model_dataframe




#Start of LSTM
#Create Dataset
model_dataset = model_dataframe.values
model_dataset = model_dataset.astype('float32')
#print(model_dataset)

#Normalization
scaler = MinMaxScaler()

close_price = model_dataframe.Close.values.reshape(-1, 1)

scaled_close = scaler.fit_transform(close_price)

#print(scaled_close.shape)
#print(np.isnan(scaled_close).any())

scaled_close = scaled_close[~np.isnan(scaled_close)]

scaled_close = scaled_close.reshape(-1, 1)

#print(np.isnan(scaled_close).any())

#Preprocessing

SEQ_LEN = 2

def to_sequences(data, seq_len):
    d = []

    for index in range(len(data) - seq_len):
        d.append(data[index: index + seq_len])

    return np.array(d)

def preprocess(data_raw, seq_len, train_split):

    data = to_sequences(data_raw, seq_len)

    #num_train = int(train_split * data.shape[0])

    X_train = data[:5, :-1, :]
    y_train = data[:5, -1, :]

    X_test = data[5:, :-1, :]
    y_test = data[5:, -1, :]

    return X_train, y_train, X_test, y_test

X_train, y_train, X_test, y_test = preprocess(scaled_close, SEQ_LEN, train_split = 0.875)

print(X_train.shape)


print(X_test.shape)


#model

DROPOUT = 0.2
WINDOW_SIZE = SEQ_LEN - 1

model = keras.Sequential()

model.add(Bidirectional(LSTM(WINDOW_SIZE, return_sequences=True),input_shape=(WINDOW_SIZE, X_train.shape[-1])))
model.add(Dropout(rate=DROPOUT))
model.add(Bidirectional(LSTM((WINDOW_SIZE * 2), return_sequences=True)))
model.add(Dropout(rate=DROPOUT))
model.add(Bidirectional(LSTM(WINDOW_SIZE, return_sequences=False)))
model.add(Dense(units=1))
model.add(Activation('linear'))

model.compile(
    loss='mean_squared_error', 
    optimizer='adam'
)
BATCH_SIZE = 6
history = model.fit(
    X_train, 
    y_train, 
    epochs=200, 
    batch_size=BATCH_SIZE, 
    shuffle=False,
    validation_split=0.1
)

model.evaluate(X_test, y_test)


plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()


y_hat = model.predict(X_test)

y_test_inverse = scaler.inverse_transform(y_test)
y_hat_inverse = scaler.inverse_transform(y_hat)

print("Predicted Price: " , y_hat_inverse)
print("Actual Price: ", bs4_realtimeprice('Bitcoin'))
plt.show()

#obtaining real time price using google query and comparing it to predicted value
btcrt_price = bs4_realtimeprice("Bitcoin").split(" ")[0]
btcrt_price = btcrt_price[0:2] + btcrt_price[3:]
p_error = ((y_hat_inverse - float(btcrt_price))/ (y_hat_inverse))*100
print("Percent Error: ", p_error, "%")