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
    "cookie": "buvid3=60F50A2C-2766-B0D7-D216-2BC9E988FE0B81766infoc; i-wanna-go-back=-1; _uuid=26EFE6E3-413B-F7110-A79C-310F10F23D6A1782150infoc; buvid_fp_plain=undefined; DedeUserID=380083993; DedeUserID__ckMd5=c8f9dbed99b291d8; rpdid=|(ku|RlRY|)l0J'uYYu)l|Rk~; b_ut=5; nostalgia_conf=-1; hit-dyn-v2=1; CURRENT_BLACKGAP=0; b_nut=100; LIVE_BUVID=AUTO9516628119345489; buvid4=E96741AA-CFBB-31F7-F3CB-7EC80150B27634543-022062512-%2BsPn6cl6xMm6h6XytsLrBhicazmmi5bHCe%2FD0qUsI14IM4N29aTrdA%3D%3D; fingerprint=70aed375b9df775d6fc3ebdad06fdf13; bp_video_offset_380083993=714162197173895200; buvid_fp=70aed375b9df775d6fc3ebdad06fdf13; SESSDATA=973a6b5b%2C1681355895%2C7f722%2Aa2; bili_jct=0996a93ed1fa62e1a27aa41d40c26a8b; sid=8439udc9; CURRENT_QUALITY=120; bsource=search_bing; b_lsid=22AD10108B_183DC67D0FB; PVID=1; CURRENT_FNVAL=16; innersign=0",
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
