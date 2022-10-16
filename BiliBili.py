import sys
import requests
import time
import json
import csv
import datetime

pop_web = 'https://api.bilibili.com/x/web-interface/popular'
header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.42",
    "Reffer": "https://www.bilibili.com/",
    "cookie": "sth",
}


def GetList(PopList=[]):
    for i in range(1, 4):
        param = {'ps': '20', 'pn': i}
        content = requests.get(url=pop_web, headers=header, params=param)
        content.close()
        PopList = PopList + json.loads(content.text)['data']['list']
    return PopList


def Form(PopInfo):
    global ProcessData
    title = PopInfo['title']
    link = PopInfo['short_link']
    owner = PopInfo['owner']['name']
    pubinfo = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(PopInfo['pubdate']))
    desc = PopInfo['desc']
    if desc == '-' or desc == '':
        desc = 'None'
    stat = PopInfo['stat']
    view = stat['view']
    like = stat['like']
    share = stat['share']
    subtitle = stat['danmaku']
    favorite = stat['favorite']
    coin = stat['coin']
    tname = PopInfo['tname']
    feature = PopInfo['rcmd_reason']['content']
    if feature == '':
        feature = 'None'
    ProcessData.append(
        {
            '标题': title,
            '链接': link,
            'UP': owner,
            '分区': tname,
            '稿件上传时间': pubinfo,
            '简介': desc,
            '播放量': view,
            '点赞数': like,
            '硬币数': coin,
            '收藏数': favorite,
            '分享数': share,
            '弹幕数': subtitle,
            'TAG': feature,
        }
    )


HeadData = [
    '标题',
    '链接',
    'UP',
    '分区',
    '稿件上传时间',
    '简介',
    '播放量',
    '点赞数',
    '硬币数',
    '收藏数',
    '分享数',
    '弹幕数',
    'TAG',
]
PopList = GetList()
ProcessData = []
for i in PopList:
    Form(i)
with open(
    '{}/../data/热门{}.csv'.format(
        sys.path[0], datetime.datetime.now().strftime("%Y-%m-%d")
    ),
    'w',
    encoding='utf-8-sig',
    newline='',
) as f:
    writer = csv.DictWriter(f, HeadData)
    writer.writeheader()
    writer.writerows(ProcessData)
