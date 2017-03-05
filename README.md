The repository was created for recruitment purposes. This project was created in purpose of passing the university course. The motivation was also to practise Python.

# Project description
## General outline of the project
The purpose of this project is to present how tweets that give either positive or negative feedback correlate with stock prices of the Google Inc. Actually project is finished and not longer supported.

## How it works?
Program receive tweets every time new tweet with #Google hashtag arise. Afterwards program makes use of the Naive Bayes Classifier to classify received tweet (more about this process in implementation section) as positive or negative opinion. Next program saves tweet to the file where all classified tweets data are stored. Classifier accuracy is about 68% (20% random choose data leave for testing, other 80% used as training data). Simultaneously  every new classified tweet is send to plot.ly where is express at real time classified tweets chart. Additionally every day program takes data from last 30 days and then for every day compute the ratio that express positive classified tweets contribution in all tweets from particular day. Afterwards program downloads information about closing stock prices of Google Inc. for this period, puts ratios and prices at one chart and then streams everything up to plot.ly where you can see results of analysis in real time.

## More detailed description
Classifier used in this project is Naive Bayes Classifier supported by nltk module. Classifier firstly needed to be trained. Data set used as training data was taken from [here](http://help.sentiment140.com/for-students). This data set reflect tweets classified as positive or negative. 5000 positive tweets and 5000 negative tweets was used to train classifier.

Training of the classifier require some data preprocessing. Firstly for each tweet from data set program retrieve sequence of characters. Then, program put this text to tokenization process. That means every single word, emoticon or link is taken from the text and exist in list as single object called token. Then links and other useless  remainings from this set of tokens are removed to simplify further processing. Stop words like „and”, „or”, „this” are also removed. List of stop words is taken from nltk stopwords corpus. Afterwards every set of tokens from training data is an argument to function that create list of tokens and its frequency of appearance. After this program have a list of tokens ordered by its frequency. Another  function retrieve features of each set of tokens. That means every token in current set of tokens from this particular tweet is compared to all words in list created before and indicates whenever token exist in list of tokens ordered by its frequency of appearance or not. So then program extract features from every set of tokens. That gives prepared training set that contains set of specific tokens and label assigned to this set which can be „positive” or „negative”. Prepared training set can now be used as a dictionary for classifier. Classifier is not perfect. We can even say is „little off” because it can’t say if particular tweet is neutral or how positive it is. It can only say that the tweet is positive, but we don’t have „power” of its positive impact.

When new tweet arrives, its text is processed. Processing consist of tokenization like before. Then stop words and links are removed. Afterwards like in process of training classifier current set of tokens is put as argument to function that retrieve features of this set of tokens but this time the label of this set is unknown. After this program put this data to classifier which classifies this tweet as positive or negative. When tweet is classified then its classification and date of the tweet creation is written to a file which is the basis for further processing. After this data about current tweet is put to buffer which is used to send data to the plot.ly. 

Every day at 9:00 a.m. program loads data from file that contains classification dates from last 30 days. Then with pandas module program samples data to one day sets and counts positive and negative classification to compute ratio for each day that express positive tweets contribution to all tweets. Before this, program requests pandas to call yahoo for stock prices and save it to the list. When tweets ratios and stock prices are prepared, program starts streaming it to plot.ly making chart that reveal how opinion about company correlates to information about stock prices.

## Results
All results are presented at plot.ly [here](https://plot.ly/~piruet/2/) and [here](https://plot.ly/~piruet/3/)

Sample screenshots:
![plotly1](https://cloud.githubusercontent.com/assets/24795433/23591617/3c3e6a10-01f3-11e7-9df1-8ce447891cc7.png)

Info:
Gaps between blue dots reveal days when stock market is closed. Gaps between orange dots reveal days when program didn’t work because of crashes. Unfortunately current results can’t reveal some interesting correlation or information because not long enough time passed when program was working.

## Sources
- http://www.laurentluce.com/posts/twitter-sentiment-analysis-using-python-and-nltk/
- http://help.sentiment140.com/for-students
- https://marcobonzanini.com/2015/03/02/mining-twitter-data-with-python-part-1/ (parts 1-7)
- Pandas, Plotlym and Python documentation

## Author
Mateusz Krogul
