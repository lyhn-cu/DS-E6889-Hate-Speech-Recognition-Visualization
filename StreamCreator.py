from twython import TwythonStreamer
import socket


# Filter out unwanted data
def process_tweet(tweet):
    d = {}
    d['hashtags'] = [hashtag['text'] for hashtag in tweet['entities']['hashtags']]
    d['text'] = tweet['text']
    d['user'] = tweet['user']['screen_name']
    d['user_loc'] = tweet['user']['location']
    return d


class MyStreamer(TwythonStreamer):
    cnt = 0

    def connect(self, port):
        TCP_IP = "127.0.0.1"
        TCP_PORT = port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((TCP_IP, TCP_PORT))
        s.listen(1)
        print("Waiting for TCP connection...")
        self.conn, self.addr = s.accept()
        print("Connected... Starting getting tweets.")

    def send_to_socket(self, packet):
        self.conn.send(packet.encode('utf-8'))

    # Received data
    def on_success(self, data):
        self.cnt += 1
        # Only collect tweets in English
        if data['lang'] == 'en':
            print(data['text'])
            self.send_to_socket(data['text']+"\n")
            print("PKT " + str(self.cnt) + " sent.")

    # Problem with the API
    def on_error(self, status_code, data):
        print(status_code, data)
        print('Error causes disconnection.')
        self.disconnect()


class StreamCreator:
    credentials = {}
    # credentials['CONSUMER_KEY'] = 'OiZ2nKMG2t1kO6D4FSODpuEzs'
    # credentials['CONSUMER_SECRET'] = 'UeGjjrdzeIL9ZYPr9Z00OALwW480bdX5LqyPATuNJX5wUrTyCn'
    # credentials['ACCESS_TOKEN'] = '1056244042835652610-SuIkLiXhvAD6zflT2pTZNL5UISNhpo'
    # credentials['ACCESS_SECRET'] = 'vQQIUrgf1IUl6aEdavNEpoPaNTaevltKjl9cFNiwNUKlq'

    credentials['CONSUMER_KEY'] = '00cMpGPDFBlqs39hCpZXLRWHk'
    credentials['CONSUMER_SECRET'] = 'MrMHRqBGw9c7OzfV70vhsjGGYiYCbjDsVQuGO94Y6E27GOWaPF'
    credentials['ACCESS_TOKEN'] = '1052242995951689728-eRfUJHsidZDVkDOK9b5DcWGP8iF7h3'
    credentials['ACCESS_SECRET'] = 'nEuuWYkXV8ZALioaXz7cmdmv30fetbXgZ40ylMjN7GIKQ'
    cnt = 0

    def __init__(self):
        self.stream = MyStreamer(self.credentials['CONSUMER_KEY'], self.credentials['CONSUMER_SECRET'],
                            self.credentials['ACCESS_TOKEN'], self.credentials['ACCESS_SECRET'])

    def start(self, port, keyword, filter_level='none'):
        # Start the stream
        trackvalue = keyword
        port = port
        self.stream.connect(port)
        #filter_level='none')
        self.stream.statuses.filter(track=trackvalue, languages='en', stall_warnings='true', filter_level=filter_level)

