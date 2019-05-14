import pyrebase
from collections import Counter
import json

# Temporarily replace quote function
def noquote(s):
    return s


pyrebase.pyrebase.quote = noquote


class DBFireBase:
    def __init__(self, keyword):
        config = {
            "apiKey": "xig5solXyTpnh0xojzx2N0uB32EFXX10elyjOHlY",
            "authDomain": "HateSpeech.firebaseapp.com",
            "databaseURL": "https://hatespeech-ds.firebaseio.com",
            "storageBucket": "HateSpeech.appspot.com"
        }

        self.keyword = keyword
        firebase = pyrebase.initialize_app(config)
        self.auth = firebase.auth()
        self.db = firebase.database()

    def get_word_cloud(self):
        res = self.db.child(self.keyword).child("word_cloud").get().val()
        return res

    def update_word_cloud(self, add_wc):
        print("in update")
        match_wc = {"fuck":"f**k",
                    "fucks":"f**ks",
                    "fucked":"f**ked",
                    "bitch":"b**ch",
                    "bitches":"b**ches",
                    "nigga":"n**ga",
                    "niggas":"n**gas",
                    "ass":"a*s",
                    "shit":"sh*t",
                    "dick":"d**k",
                    }
        for k,v in match_wc.items():
            if k in add_wc:
                add_wc[v] = add_wc.pop(k)
        orig_wc = self.get_word_cloud() or {}
        new_wc = Counter(orig_wc) + Counter(add_wc)
        self.db.child(self.keyword).child("word_cloud").set(new_wc)

    def get_text_result(self, limit=50):
        txt_res = self.db.child(self.keyword).child("txt_res").order_by_key().limit_to_first(limit).get().val()
        res = list(txt_res.values())
        return res

    def push_text_result(self, txt_res):
        # data = {}
        # for ele in txt_res:
        #     data[self.db.generate_key()]=ele
        # self.db.child(self.keyword).child("txt_res").push(data)

        for ele in txt_res:
            # data[self.db.generate_key()]=ele
            self.db.child(self.keyword).child("txt_res").push(ele)

        # for ele in txt_res:
        #     self.db.child(self.keyword).child("txt_res").push({self.db.generate_key():ele})

# db = DBFireBase("nigga")
# rs = {"text":"aaaaaaaa", "classification":2}
# db.push_text_result(rs)
