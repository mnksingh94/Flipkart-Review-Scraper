from flask import Flask, render_template, request, jsonify
from flask_cors import CORS, cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo

app =  Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        searchString = request.form['content'].replace(" ", "")
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017")
            db =dbConn['crawlerDB']
            reviews = db[searchString].find({})
            print(reviews.count())
            if reviews.count() > 0:
                return render_template('results.html', reviews=reviews)
            else:
                flipkart_url = "https://www.flipkart.com/search?q=" + searchString
                uClient = uReq(flipkart_url)
                flipkartPage = uClient.read()
                uClient.close()
                flipkart_html = bs(flipkartPage, "html.parser")
                bigboxes = flipkart_html.find_all("div", {"class": "_1AtVbE col-12-12"})
                del bigboxes[0:3]
                box = bigboxes[0]
                productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
                prodRes = requests.get(productLink)
                prod_html = bs(prodRes.text, "html.parser")
                commentboxs = prod_html.find_all('div', {'class': "_16PBlm"})

                table = db[searchString]
                reviews = []
                for commentbox in commentboxs:
                    try:
                        name = commentbox.div.div.find_all('p', {'class':'_2sc7ZR _2V5EHH'})[0].text
                    except:
                        name = 'No name'
                    try:
                        rating = commentbox.div.div.div.div.text
                    except:
                        rating = 'No rating'

                    try:
                        commentHead = commentbox.div.find_all('p', {'class':'_2-N8zT'})[0].text
                    except:
                        commentHead = 'No comment heading'

                    try:
                        comtag = commentbox.div.div.find_all('div', {'class':''})
                        custComment = comtag[0].div.text
                    except:
                        custComment = 'no customer comment'

                    mydict  = {'Product':searchString, 'Name':name, 'Rating':rating, 'CommentHead': commentHead,
                               'Comment':custComment}
                    x = table.insert_one(mydict)
                    reviews.append(mydict)
                return render_template('results.html', reviews=reviews)
        except:
            return 'something is wrong'
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(port=8000, debug=True)
