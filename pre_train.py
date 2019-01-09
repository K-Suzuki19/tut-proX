# -*- coding: utf-8 -*-
"""pre_train.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1y-bZC3j5aA0uuv88DUmKeX3sULtf116C

# 各種インストール&インポート
"""

###各種インストール＆インポート

#MeCabのインストール
!apt-get -q -y install swig
!apt-get install mecab libmecab-dev mecab-ipadic-utf8
!pip install mecab-python3

#Chainerのインストール
!pip install chainer
!pip install cupy-cuda92

#Janomeのインストール
!pip3 install janome

"""## インポート"""

import datetime
import numpy as np
import chainer
import chainer.functions as F
import chainer.links as L
import MeCab

"""## GPUのセット"""

###GPUのセット

from chainer import Variable, optimizers, Chain
#import cuda

gpu = 0
if gpu >= 0: # numpyかcuda.cupyか
    xp = chainer.cuda.cupy
    chainer.cuda.get_device(gpu).use()
else:
    xp = np

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

"""# 学習データを元データ＋スタイルデータにする"""

###学習データを元データ(対話文のデータセット)＋スタイルデータ(キャラクターの対話文のデータセット)にする


main_file = '' #対話文のデータセットのファイル名(npy形式)
style_file = '' #キャラクターの対話文のデータセットのファイル名(npy形式)

#npyロード
main_data = np.load(main_file)
style_char = np.load(style_file)

#対話文のデータセットとキャラクターの対話文のデータセット,それぞれの対話数確認

print(len(main_data),len(style_char))

#対話文のデータセットとキャラクターの対話文のデータセットを結合

data = []
data = np.concatenate([main_data,style_char], axis=0)

#結合後の対話数確認

len(data)

"""# クラス定義(定義をまとめた.pyをimport)"""

#seq2seq_class.pyをロード

import seq2seq_class

#seq2seq_class.pyを実行

run seq2seq_class.py

"""# 学習"""

###学習

#学習に必要な設定など

embed_size = 200
hidden_size = 1000
batch_size = 128 # ミニバッチ学習のバッチサイズ数
batch_col_size = 10
epoch_num = 20 # エポック数
N = len(data)# 教師データの数

# 教師データの読み込み
data_converter = DataConverter(batch_col_size=batch_col_size) # データコンバーター
data_converter.load(data) # 教師データ読み込み
vocab_size = len(data_converter.vocab) # 単語数

# モデルの宣言
model = AttSeq2Seq(vocab_size=vocab_size, embed_size=embed_size, hidden_size=hidden_size, batch_col_size=batch_col_size)
opt = chainer.optimizers.Adam()
opt.setup(model)
opt.add_hook(chainer.optimizer.GradientClipping(5))

if gpu >= 0:
  model.to_gpu(gpu)

model.reset()

#辞書に登録された単語数確認

vocab_size

#学習を回す

st = datetime.datetime.now()
for epoch in range(epoch_num):
    
    # ミニバッチ学習
    perm = np.random.permutation(N) # ランダムな整数列リストを取得
    total_loss = 0
    
    for i in range(0, N, batch_size):
        enc_words = data_converter.train_queries[perm[i:i+batch_size]]
        dec_words = data_converter.train_responses[perm[i:i+batch_size]]
        model.reset()
        loss = model(enc_words=enc_words, dec_words=dec_words, train=True)
        loss.backward()9l
        loss.unchain_backward()
        total_loss += loss.data
        opt.update()
        
    if (epoch+1)%1 == 0:
        ed = datetime.datetime.now()
        print("epoch:\t{}\ttotal loss:\t{}\ttime:\t{}".format(epoch+1, total_loss, ed-st))
        st = datetime.datetime.now()

#対話文生成のための関数定義

def predict(model, query):
  enc_query = data_converter.sentence2ids(query, train=False)
  dec_response = model(enc_words=enc_query, train=False)
  response = data_converter.ids2words(dec_response)
  print(query, "=>", response)

#対話文生成

predict(model, "") #""内に発話を入力
predict(model, "")
predict(model, "")

"""# 学習モデルの保存"""

###学習モデルの保存(転移学習の際に使用する)

from chainer import serializers

model.to_cpu() # CPUで計算できるようにしておく
serializers.save_npz("保存したいモデル名(拡張子は.npz)", model) #npz形式で書き出し

#以下はColaboratoryからGoogleDriveのマイドライブに保存する方法

import google.colab
import googleapiclient.discovery
import googleapiclient.http

google.colab.auth.authenticate_user()
drive_service = googleapiclient.discovery.build('drive', 'v3')

saving_filename = "" #セーブしたいファイル名(拡張子は.npz)

file_metadata = {
  'name': saving_filename,
  'mimeType': 'application/octet-stream'
}
media = googleapiclient.http.MediaFileUpload(saving_filename, 
                        mimetype='application/octet-stream',
                        resumable=True)
created = drive_service.files().create(body=file_metadata,
                                       media_body=media,
                                       fields='id').execute()

!mkdir -p drive
!google-drive-ocamlfuse drive