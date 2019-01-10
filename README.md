# キャラクターらしい対話文の生成

大学のプロジェクト実習で深層学習の技術を使って何かを作るということで、対話文生成(文章生成)のコードを作成しました。
今回はseq2seqという技術を使って対話文(発話と応答がセットになっているもの)のデータセットを学習用データとして事前学習、転移学習を行いました。  
学習用コードに関しては以下の2つのWebページに載っているものを参考にしました。  
* < https://github.com/Gin04gh/datascience/blob/master/samples_deeplearning_python/attention_seq2seq.ipynb > 
* < https://github.com/kawamix/seq2seq-haruka-amami-01 > 


## データセットについて
学習用のテキストデータは明大会話コーパス( <https://mmsrv.ninjal.ac.jp/nucc/> )をダウンロードして使用しました。  
このデータセットを成形するコードは( <https://github.com/knok/make-meidai-dialogue> )　からお借りしました。  

また、データ数を増やすため初対面の人たちでの会話( <http://nihongo.hum.tmu.ac.jp/mic-j/kaiwa/> にあるguuzen.csv)も追加し、データセットとしました。  

キャラクターらしい対話文にするためのデータはスマイルプリキュア！のアニメセリフ集が載っているWebページ(<http://smileprecureserifu.blog.jp/>)から手作業でコピーし、データとしました。  


## 各プログラム,ファイルについて
* pre_train.py       :事前学習用のコード
* seq2seq_class.py   :学習に必要なseq2seqクラスをまとめたコード
* smile_all.txt      :スマイルプリキュアのセリフを全部まとめたテキストデータ
* style_data.py      :スタイル付与用のデータを学習用に成形するためのコード
* transfer_train.py  :転移学習用のコード

## 参考文献
* <https://mmsrv.ninjal.ac.jp/nucc/> :明大会話コーパス
* <http://nihongo.hum.tmu.ac.jp/mic-j/kaiwa/> :初対面の会話-基礎的方法と公開データ-
* <http://smileprecureserifu.blog.jp/> :スマイルプリキュア！セリフ集
* <https://github.com/knok/make-meidai-dialogue> :明大会話コーパスのデータ成形コード
* <https://github.com/Gin04gh/datascience/blob/master/samples_deeplearning_python/attention_seq2seq.ipynb> :seq2seqのAttentionモデル
* <https://github.com/kawamix/seq2seq-haruka-amami-01> :転移学習を用いた天海春香AI
* <http://muscle-keisuke.hatenablog.com/entry/2017/12/13/125951> :LINEでみりあちゃんと会話できるようにした
