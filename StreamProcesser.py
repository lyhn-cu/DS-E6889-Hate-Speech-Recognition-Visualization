from pyspark import SparkConf,SparkContext
from pyspark.streaming import StreamingContext
import sys
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as VS
from nltk.stem.porter import *
from pyspark.sql import Row,SQLContext
import time as ttime
import nltk
from DBFireBase import DBFireBase

stemmer = PorterStemmer()
sentiment_analyzer = VS()
cnt = 0
stopwords = nltk.corpus.stopwords.words("english")
other_exclusions = ["#ff", "ff", "rt"]
stopwords.extend(other_exclusions)


# tokenize for wordcloud(no stemming)
def wc_tokenize(tweet):
    tokens = []
    tweet = " ".join(re.split("[^a-zA-Z]+", tweet.lower())).strip()
    for t in tweet.split():
        if t not in stopwords:
            tokens += [t]
    return tokens


from HateSpeechCLF import *
from HateSpeechCLF import _tokenize, _preprocess


def aggregate_tags_count(new_values, total_sum):
    return sum(new_values) + (total_sum or 0)


# Filter out unwanted data
def process_tweet(tweet):
    d = {}
    d['hashtags'] = [hashtag['text'] for hashtag in tweet['entities']['hashtags']]
    d['text'] = tweet['text']
    d['user'] = tweet['user']['screen_name']
    d['user_loc'] = tweet['user']['location']
    return d


class StreamProcesser:
    def get_sql_context_instance(self, spark_context):
        if 'sqlContextSingletonInstance' not in globals():
            globals()['sqlContextSingletonInstance'] = SQLContext(spark_context)
            return globals()['sqlContextSingletonInstance']

    def process_rdd(self, time, rdd):
        t0 = ttime.time()
        print("----------- %s -----------" % str(time))
        print("\n")
        try:
            wc_list = rdd.collect()
            print("Collect succeed.")
            print(wc_list)
            if wc_list:
                print("Batch not empty.")
                # for wc in wc_list:
                #     word_count[wc[0]]=wc[1]
                word_count = dict(wc_list)
                print("word_count",word_count)
                t1 = ttime.time()
                self.db.update_word_cloud(word_count)
                print("Time for collection = " + str(t1-t0))
                t2 = ttime.time()
                print("Time for uploading to db = " + str(t2-t1))
            else:
                print("\nNothing in this batch.")
        except Exception as ee:
            print(ee)
            e = sys.exc_info()[0]
            print("Error: %s" % e)

    def process_rdd2(self, time, rdd):
        global cnt
        try:
            text_list = rdd.collect()
            print("Collect succeed. //predict")
            print(text_list)
            txt_res = []
            if text_list:
                print("Batch not empty. //predict")
                print(len(text_list))
                for ele in text_list:
                    txt = ele[0]
                    res = int(ele[1][0])
                    if txt:
                        cnt += 1
                        txt_res += [{"text":txt, "classification":res}]
                print(str(cnt) + "non empty texts processed.")
                # print out text and result for this batch.
                # print("//////////////////////////////////////////////////////////////////////////////")
                # print(txt_res)
                # print("//////////////////////////////////////////////////////////////////////////////")

                self.db.push_text_result(txt_res)
                print("\nSent to FB. //predict")
            else:
                print("\nNothing in this batch. //predict")
        except Exception as ee:
            print(ee)
            e = sys.exc_info()[0]
            print("Error: %s" % e)

    def start(self, port, keyword, timeout=60):
        print("port", port)
        print("keyword", keyword)
        sc = SparkContext('local[3]',"TwitterStreamApp" + str(port))
        sc.setLogLevel("ERROR")
        # create the Streaming Context from the above spark context with interval size 3 seconds
        ssc = StreamingContext(sc, 3)
        # # setting a checkpoint to allow RDD recovery
        # ssc.checkpoint("checkpoint_TwitterApp" + str(port))
        # read data from port
        self.db = DBFireBase(keyword)
        dataStream = ssc.socketTextStream("127.0.0.1", port)
        # processing
        # split each tweet into words
        tokens = dataStream.flatMap(lambda line: wc_tokenize(_preprocess(line)))

        # count each word
        word_count = tokens.map(lambda x: (x, 1))
        word_counts = word_count.reduceByKey(lambda a, b: a+b)

        # hate speech prediction
        result = dataStream.map(lambda line: (line, predict(get_feats(np.asarray([line], dtype='U')))))

        # upload to Firebase
        word_counts.foreachRDD(self.process_rdd)
        result.foreachRDD(self.process_rdd2)
        ssc.start()
        # wait for timeout default 60s
        ssc.awaitTerminationOrTimeout(timeout)
        ssc.stop()
