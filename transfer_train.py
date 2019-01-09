# -*- coding: utf-8 -*-
"""transfer_train.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ri6YRX-L1BCHdR5jgZfurpJEyQZ1t8M9

# 各種インストール
"""

###各種インストール

#Chainerのインストール
!pip install chainer
!pip install cupy-cuda92

#MeCabのインストール
!apt-get -q -y install swig
!apt-get install mecab libmecab-dev mecab-ipadic-utf8
!pip install mecab-python3

#janomeのインストール
!pip3 install janome

"""# Google Driveからマウント"""

from google.colab import drive
drive.mount('/content/gdrive')

!ls ./gdrive/'My Drive'/"Colab Notebooks"

"""### データセット移動"""

ls ./gdrive/'My Drive'/'Colab Notebooks'/'アップロードするデータ'

#今いるディレクトリにデータをコピーする(パスは一例です)

!cp ./gdrive/'My Drive'/'Colab Notebooks'/'アップロードするデータ'/'data.npy' ./data.npy
!cp ./gdrive/'My Drive'/'Colab Notebooks'/'アップロードするデータ'/'seq2seq_class.py' ./seq2seq_class.py
!cp ./gdrive/'My Drive'/"Colab Notebooks"/'アップロードするデータ'/'pre_model.npz' ./pre_model.npz
!cp ./gdrive/'My Drive'/"Colab Notebooks"/'アップロードするデータ'/'style_akane.npy' ./style_akane.npy

ls

"""#転移学習

## 事前学習引継ぎ

### 学習データを元データ(対話文のデータセット)＋スタイルデータ(キャラクターの対話文のデータセット)にする
"""

#各種ファイル
main_file = '' #対話文のデータセットのファイル名(npy形式)
style_file = '' #キャラクターの対話文のデータセットのファイル名(npy形式)

#npyロード
main_data = np.load(main_file)
style_char = np.load(style_file)

"""### 単語辞書登録用にdata.npyとstyle_data.npyを合体"""

#各データの対話数確認
print(len(s_data),len(data))

a_data = []
a_data = np.concatenate([data,s_data], axis=0)

#データが合体できているか確認
len(a_data)

"""## 転移学習メイン"""

#各種インポート

import chainer
from chainer import links as L
from chainer import functions as F
from chainer import optimizers
from collections import Counter
import numpy as np
from chainer import cuda
import random
import math
from datetime import datetime
import yaml
from janome.tokenizer import Tokenizer
#import util

from logging import getLogger, StreamHandler, INFO, DEBUG

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
logger.setLevel(INFO)
logger.addHandler(handler)

"""### 事前学習で使ったエンコーダ、デコーダの定義を使う"""

import seq2seq_class

run seq2seq_class.py

"""#### TODO 1: AttSeq2Seq クラスへ，保存した学習済みモデルをロードする,DataConverter クラスもロードする．"""

#GPUのセット
from chainer import cuda 

gpu = 0
if gpu >= 0: # numpyかcuda.cupyか
    xp = chainer.cuda.cupy
    chainer.cuda.get_device(gpu).use()
else:
    xp = np

embed_size = 200
hidden_size = 1000
batch_size = 128 # ミニバッチ学習のバッチサイズ数
batch_col_size = 10
epoch_num = 20 # エポック数
N = len(a_data)# 教師データの数


# 教師データの読み込み
data_converter = DataConverter(batch_col_size=batch_col_size) # データコンバーター
data_converter.load(a_data) # 教師データ読み込み
vocab_size = len(data_converter.vocab)

#pre_vocab = data_converter.vocab

from chainer import serializers

pre_model = 'ファイル名' #事前学習モデルのファイル名入力(拡張子が.npzのもの)

model = AttSeq2Seq(vocab_size=vocab_size, embed_size=embed_size, hidden_size=hidden_size, batch_col_size=batch_col_size) # saveした時と同じ構成
serializers.load_npz(pre_model, model) # 事前学習モデルの情報をmodelに読み込む

opt = chainer.optimizers.Adam()
opt.setup(model)
opt.add_hook(chainer.optimizer.GradientClipping(5))

"""#### TODO 2 : ロードしたAttSeq2Seq モデルと，DataConverter クラスを使って，対話文を生成する"""

def predict(model, query):
  enc_query = data_converter.sentence2ids(query, train=False)
  dec_response = model(enc_words=enc_query, train=False)
  response = data_converter.ids2words(dec_response)
  print(query, "=>", response)

len(data_converter.vocab)

#対話文生成

predict(model, "") #""内に発話を入力
predict(model, "")
predict(model, "")

"""#### TODO 3 : 転移先のデータ(style データ) をDataConverter に入れる"""

#事前学習で作成した単語辞書はそのままに、転移学習のデータセットをロードできるようにクラスを書き換える

class DataConverter:

  def __init__(self, batch_col_size):
        """クラスの初期化
        Args:
            batch_col_size: 学習時のミニバッチ単語数サイズ
        """
        self.mecab = MeCab.Tagger() # 形態素解析器
        #n_path = '/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd' #追加した
        #self.mecab = MeCab.Tagger(n_path)  #追加した
        self.vocab = pre_vocab # 単語辞書
        self.batch_col_size = batch_col_size
  
  def load(self, data):
        """学習時に、教師データを読み込んでミニバッチサイズに対応したNumpy配列に変換する
        
        Args:
            data: 対話データ
        """
        # 単語辞書の登録
        self.vocab = pre_vocab
        for d in data:
            sentences = [d[0][0],d[1][0]] # 入力文、返答文
            for sentence in sentences:
                sentence_words = self.sentence2words(sentence) # 文章を単語に分解する
                for word in sentence_words:
                    if word not in self.vocab:
                        self.vocab[word] = len(self.vocab)
        # 教師データのID化と整理
        queries, responses = [], []
        for d in data:
            query, response = d[0][0], d[1][0]#  エンコード文、デコード文
            queries.append(self.sentence2ids(sentence=query, train=True, sentence_type="query"))
            responses.append(self.sentence2ids(sentence=response, train=True, sentence_type="response"))
        self.train_queries = xp.vstack(queries)
        self.train_responses = xp.vstack(responses)

  def sentence2words(self, sentence):
        """文章を単語の配列にして返却する
        
        Args:
            sentence: 文章文字列
        """
        sentence_words = []
        for m in self.mecab.parse(sentence).split("\n"): # 形態素解析で単語に分解する
            w = m.split("\t")[0].lower() # 単語
            if len(w) == 0 or w == "eos": # 不正文字、EOSは省略
                continue
            sentence_words.append(w)
        sentence_words.append("<eos>") # 最後にvocabに登録している<eos>を代入する
        return sentence_words
      
  def sentence2ids(self, sentence, train=True, sentence_type="query"):
        """文章を単語IDのNumpy配列に変換して返却する
        
        Args:
            sentence: 文章文字列
            train: 学習用かどうか
            sentence_type: 学習用でミニバッチ対応のためのサイズ補填方向をクエリー・レスポンスで変更するため"query"or"response"を指定　
        Returns:
            ids: 単語IDのNumpy配列
        """
        ids = [] # 単語IDに変換して格納する配列
        sentence_words = self.sentence2words(sentence) # 文章を単語に分解する
        for word in sentence_words:
            if word in self.vocab: # 単語辞書に存在する単語ならば、IDに変換する
                ids.append(self.vocab[word])
            else: # 単語辞書に存在しない単語ならば、<unknown>に変換する
                ids.append(self.vocab["<unknown>"])
        # 学習時は、ミニバッチ対応のため、単語数サイズを調整してNumpy変換する
        if train:
            if sentence_type == "query": # クエリーの場合は前方にミニバッチ単語数サイズになるまで-1を補填する
                while len(ids) > self.batch_col_size: # ミニバッチ単語サイズよりも大きければ、ミニバッチ単語サイズになるまで先頭から削る
                    ids.pop(0)
                ids = xp.array([-1]*(self.batch_col_size-len(ids))+ids, dtype="int32")
            elif sentence_type == "response": # レスポンスの場合は後方にミニバッチ単語数サイズになるまで-1を補填する
                while len(ids) > self.batch_col_size: # ミニバッチ単語サイズよりも大きければ、ミニバッチ単語サイズになるまで末尾から削る
                    ids.pop()
                ids = xp.array(ids+[-1]*(self.batch_col_size-len(ids)), dtype="int32")
        else: # 予測時は、そのままNumpy変換する
            ids = xp.array([ids], dtype="int32")
        return ids
   
  def ids2words(self, ids):
        """予測時に、単語IDのNumpy配列を単語に変換して返却する
        
        Args:
            ids: 単語IDのNumpy配列
        Returns:
            words: 単語の配列
        """
        words = [] # 単語を格納する配列
        for i in ids: # 順番に単語IDを単語辞書から参照して単語に変換する
            words.append(list(self.vocab.keys())[list(self.vocab.values()).index(i)])
        return words

embed_size = 200
hidden_size = 1000
batch_size = 128 # ミニバッチ学習のバッチサイズ数
batch_col_size = 10
epoch_num = 20 # エポック数
N = len(s_data)# 教師データの数

# スタイルデータの読み込み
data_converter = DataConverter(batch_col_size=batch_col_size) # データコンバーター
data_converter.load(s_data) # スタイルデータ読み込み
vocab_size = len(data_converter.vocab)

# モデルの宣言
model = AttSeq2Seq(vocab_size=vocab_size, embed_size=embed_size, hidden_size=hidden_size, batch_col_size=batch_col_size)
opt = chainer.optimizers.Adam()
opt.setup(model)
opt.add_hook(chainer.optimizer.GradientClipping(5))

if gpu >= 0:
  model.to_gpu(gpu)

#model.reset()

vocab_size

"""#### TODO 4: 事前学習と同じコードを使って，データだけstyle ファイルにして，事後学習を行う．"""

st = datetime.datetime.now()
for epoch in range(epoch_num):
    
    # ミニバッチ学習
    perm = np.random.permutation(N) # ランダムな整数列リストを取得
    total_loss = 0
    
    for i in range(0, N, batch_size):
        enc_words = data_converter.train_queries[perm[i:i+batch_size]]
        dec_words = data_converter.train_responses[perm[i:i+batch_size]]
        #model.reset()
        loss = model(enc_words=enc_words, dec_words=dec_words, train=True)
        loss.backward()
        loss.unchain_backward()
        total_loss += loss.data
        opt.update()
        
    if (epoch+1)%1 == 0:
        ed = datetime.datetime.now()
        print("epoch:\t{}\ttotal loss:\t{}\ttime:\t{}".format(epoch+1, total_loss, ed-st))
        st = datetime.datetime.now()

"""#### TODO 5: 事後学習のモデルと，DataConverter クラスを使って，対話文生成してみる．"""

def predict(model, query):
  enc_query = data_converter.sentence2ids(query, train=False)
  dec_response = model(enc_words=enc_query, train=False)
  response = data_converter.ids2words(dec_response)
  print(query, "=>", response)

#対話文生成

model.to_gpu()
predict(model, "ここに任意の1文を入力")
predict(model, "")
predict(model, "")