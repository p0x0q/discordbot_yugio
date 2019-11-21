# インストールした discord.py を読み込む
import discord
import re

import requests
import bs4
import urllib
import re
import shutil

import urllib.request
import http.cookiejar
import os,os.path

import json

#実行時にクッキーを消す場合はTrue, Falseにするとプログラム終了後もクッキーが保持される。
if_delete_cookie = True
#Wikiから情報を更新したいときはこれをTrueにしてupdate_yugio_card_list()を呼び出す。
#ただし結構時間がかかる。別スレッドで定期的に更新させる手もアリ
if_update_yugio_card_list = False

class request_cookie():
    def __init__(self):
        self.cookiefile = "cookies.txt"
        self.cj = http.cookiejar.LWPCookieJar()
        if os.path.exists(self.cookiefile):
            self.cj.load(self.cookiefile)
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        urllib.request.install_opener(opener)
    
    def __del__( self ):
        self.cj.save(self.cookiefile)
        #print("Cookie saved to "+self.cookiefile)
        
    def get(self,url,headers = {
        "Upgrade-Insecure-Requests" : "1",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0",
        "Cache-Control" : "max-age=0",
    }):
        headers["Host"] = urllib.parse.urlparse(url).netloc
        headers["Referer"] = url
        #print(headers)
        req = urllib.request.Request(url, None, headers)
        response = urllib.request.urlopen(req)
        return response
    
    def post(self,url,param,headers = {
        "Upgrade-Insecure-Requests" : "1",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0",
        "Cache-Control" : "max-age=0",
    }):
        headers["Host"] = urllib.parse.urlparse(url).netloc
        headers["Referer"] = url
        #print(headers)
        param = urllib.parse.urlencode(param)
        param = param.encode('ascii')
        req = urllib.request.Request(url, param, headers,method="POST")
        response = urllib.request.urlopen(req)
        return response
#部分一致検索のリストを扱う関係
def fetch_yugio_card_list():
    result = request_cookie().post("http://yugioh-wiki.net/?cmd=search",{"word" : "《","encode_hint" : "ぷ"}).read().decode("EUC-JP","ignore")
    bs4Obj = bs4.BeautifulSoup(result,"html.parser")
    cards = bs4Obj.select("#body ul li")
    valid_cards = []
    for name in cards:
        valid_cards.append(str(name.text))
    return valid_cards
def update_yugio_card_list():
    valid_cards = fetch_yugio_card_list()
    fw = open('./cards.json',"w",encoding='utf8')
    json.dump(valid_cards,fw,ensure_ascii=False)
    fw.close()
def get_yugio_card_list():
    fr = open('./cards.json', 'r', encoding="utf8")
    valid_cards = json.load(fr)
    result = []
    for name in valid_cards:
        if re.search("《.+?》",name) != None: # cards.jsonにある中から、更にカード名とされる情報のみ
            result.append(re.sub("《|》|\s.+?$","",name)) # '《~~~》 ---' to '~~~'
    return result
def search_yugio_card_name(name,cards):
    return [r for r in cards if name in r]
#検証済みのカード名から情報を取得する関係
def fetch_yugio_card_direct(fetch_url,selecter = {
        "search_text" : "table #body pre",
    }):
    try:
        result =  request_cookie().get(fetch_url).read().decode("EUC-JP")
        print(result)
        bs4Obj = bs4.BeautifulSoup(result,"html.parser")
        texts = bs4Obj.select(selecter["search_text"])
        text = None
        #print("len:{}".format(len(texts)))
        if len(texts) >= 1:
            text = texts[0].text
        return text
    except:
        return None
def fetch_yugio_card(name):
  param = urllib.parse.quote("《{}》".format(name),encoding="EUC-JP")
  res = fetch_yugio_card_direct(r"http://yugioh-wiki.net/index.php?{}".format(param))
  print("name:{}, param:{}".format(name,param))
  return res
#secure.json関係
def secure(name):
    with open('./secure.json', 'r', encoding="utf8") as fr:
            return json.load(fr)[name]
if if_delete_cookie == True and os.path.exists("cookies.txt") == True:
    os.remove("cookies.txt")

#cards.jsonがなければサーバーからリストを取得
if os.path.exists("cards.json") == False or if_update_yugio_card_list == True:
    print("遊戯王カードリストの更新中...")
    update_yugio_card_list()

#cards.jsonからカード情報を取得
yugio_cards = get_yugio_card_list()

print("ログイン中...")


# secure.sample.jsonの中にあるYOUR_DISCORD_ACCESS_TOKENを適切な情報に書き換え、かつsecure.jsonに名前を変更してください。
TOKEN = str(secure("TOKEN"))
# 接続に必要なオブジェクトを生成
client = discord.Client()

# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')

# # メッセージ受信時に動作する処理
# @client.event
# async def on_message(message):
#     # メッセージ送信者がBotだった場合は無視する
#     if message.author.bot:
#         return
#     # 「/neko」と発言したら「にゃーん」が返る処理
#     if message.content == '/neko':
#         await message.channel.send('にゃーん')
@client.event
async def on_message(message):
    if client.user in message.mentions and client.user != message.author: # 話しかけられたかの判定と自身へのメンションを無効化
        #reply = message.author.mention + message.content # 返信メッセージの作成
        name = message.content
        name = re.sub("^.+?\s","",name)# '<@~~~> message' to 'message'

        search = search_yugio_card_name(name,yugio_cards)
        reply_list = "検索候補："
        for s in search:
            reply_list += s + ", "
        if len(search) == 0:
            reply_list = "検索候補は見つかりませんでした。"
        await message.channel.send(reply_list)
        reply = "【" + search[0] + "】" + "\r\n" + fetch_yugio_card(search[0])
        print("receive:{}, reply:{}, valid_search:{}".format(message.content,reply,search[0]))
        #reply = message.author.mention + val
        await message.channel.send(reply) # 返信メッセージを送信
#@client.event
#async def on_message(message):
    
# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)

