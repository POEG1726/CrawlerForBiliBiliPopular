import tqdm

pr = tqdm.tqdm.write
import datetime
import json
import os
import random
import re
import shutil
import string
import sys
import threading
import fake_useragent
import paramiko
import parsel
import py7zr as T7z
import requests
from requests.adapters import HTTPAdapter

requests.packages.urllib3.disable_warnings()
s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=20))
s.mount('https://', HTTPAdapter(max_retries=20))

global pbar, Config, PictureList, UploadThreadsCounter

psor = parsel.Selector
path = sys.path[0]
Timeout = None
HomeSite = 'https://www.jpmn5.cc/'
Lock = threading.Lock()
threadsmax = threading.BoundedSemaphore(5)
PictureList = []
with open('{}/../json/config.json'.format(path), 'r', encoding='utf8') as Config:
    Config = json.load(Config)


def FrontTask(Header):
    global HomeSite
    tmpvue = 'https://www.quanjixiu.top/'
    tmpvue = requests.get(url=tmpvue, timeout=Timeout, headers=Header, verify=False)
    tmpvue.encoding = 'utf8'
    tmpvue = psor(tmpvue.text).xpath('//tbody/tr/td[2]/a[1]/b/text()').get()
    if tmpvue:
        HomeSite = tmpvue
    else:
        return


def RandomString():
    number_of_strings = 1
    length_of_string = 10
    for x in range(number_of_strings):
        return ''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(length_of_string)
        )


def SortList(Organization):
    with open(
        '{}/../json/{}.json'.format(path, Organization), 'r', encoding='utf8'
    ) as tmpjson:
        try:
            data = json.load(tmpjson)
        except:
            return
    for i in range(len(data)):
        data[i]['No.'] = int(data[i]['No.'])
    with open('{}/../json/tmp.json'.format(path), 'w', encoding='utf8') as tmpjson:
        json.dump(data, tmpjson, indent=4, ensure_ascii=False)
    data = sorted(data, key=lambda r: r['No.'], reverse=True)
    with open(
        '{}/../json/{}.json'.format(path, Organization), 'w', encoding='utf8'
    ) as tmpjson:
        json.dump(data, tmpjson, indent=4, ensure_ascii=False)


def SSHClient():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    hostname = '192.168.2.4'
    port = 22
    username = 'root'
    passwd = '071126Xyf'
    ssh.connect(hostname=hostname, port=port, username=username, password=passwd)
    ssh.exec_command('''ln -s src dst''')
    ssh.close()


def Compress_and_Upload(vol, owner, Organization, title):
    Lock.acquire()
    threadsmax.acquire()
    ArchiveName = (
        path + '/../archives/' + '[' + Organization + ']' + vol + '-' + owner + '.7z'
    )
    with T7z.SevenZipFile(
        ArchiveName,
        'w',
        password='MDcxMTI2WHlm',
    ) as archive:
        archive.writeall('/nas/Girls/{}/{}'.format(Organization, title), Organization)
    os.system(
        '''bypy --processes 4 upload {} /photos/{}/'''.format(ArchiveName, Organization)
    )
    os.remove(ArchiveName)
    threadsmax.release()
    Lock.release()
    

def GetPictureUrl(DetailSite_Url: str, Header: dict):
    global PictureList
    Lock.acquire()
    DetailSite = requests.get(
        url=DetailSite_Url, timeout=Timeout, verify=False, headers=Header
    )
    DetailSite.encoding = 'utf8'
    PictureList = (
        PictureList
        + psor(DetailSite.text)
        .xpath("//article[@class='article-content']/p/img/@src")
        .getall()
    )
    Lock.release()


def DownLoadList(url: str, ua, Organization: str, Title: str):
    global pbar
    os.system(
        '''wget -q -nc --user-agent '{}' –tries=5 --method GET -P '/nas/Girls/{}/{}/' '{}' '''.format(
            ua,
            Organization,
            Title,
            url,
        )
    )
    Lock.acquire()
    pbar.update(1)
    Lock.release()
    # pass


def Crawler(
    Organization: str,
    Ends: int,
    WebLatest: int,
    LocalLatest: int,
):
    with open('{}/../json/name.json'.format(path), 'r', encoding='utf8') as tmpjson:
        try:
            NameArr = json.load(tmpjson)
        except:
            NameArr = []
    try:
        global pbar, PictureList
        if LocalLatest == WebLatest:
            pr('{}:网站未更新'.format(Organization))
            return
        else:
            pr('{}:网站已更新    {}->{}'.format(Organization, WebLatest, LocalLatest))
        LoopFlag = True
        for i in range(115, Ends):
            if LoopFlag == True:
                if i == 0:
                    InitialSite = HomeSite + Organization
                else:
                    InitialSite = (
                        HomeSite + Organization + '/page_{}.html'.format(i + 1)
                    )
                Header = {
                    'user-agent': fake_useragent.UserAgent(
                        path='{}/../json/ua.json'.format(path),
                    ).random,
                    'Connection': 'close',
                }
                res = requests.get(
                    url=InitialSite,
                    timeout=Timeout,
                    verify=False,
                    headers=Header,
                )
                res.encoding = 'utf8'
                menu = (
                    psor(res.text)
                    .xpath("//div[@class='related_posts']/ul//li/a/@href")
                    .getall()
                )
                for item in range(len(menu)):
                    menu[item] = HomeSite + menu[item]
                for j in range(len(menu)):
                    DetailSite = requests.get(
                        url=menu[j],
                        timeout=Timeout,
                        verify=False,
                        headers=Header,
                    )
                    DetailSite.encoding = 'utf8'
                    Title = str(psor(DetailSite.text).xpath("//header/h1/text()").get())
                    Title = (
                        Title.replace('_', '')
                        .replace('IMISS', 'Imiss')
                        .replace('XINGYAN', 'XingYan')
                    )
                    Title = re.sub(r'(?i)Vol.', '第', Title)
                    if '期' not in Title:
                        position = re.search(r'\d+', Title).span()
                        tmp = list(Title)
                        tmp.insert(position[-1], '期')
                        Title = ''.join(tmp)
                    if '[' not in Title:
                        Title = re.sub(r'(?i)XiuRen', "[XiuRen秀人网]", Title)
                    pr(
                        '当前:{}-{} target={}'.format(
                            Organization, re.findall(r'\d+', Title)[0], LocalLatest
                        )
                    )
                    if str(re.findall(r'\d+', Title)[0]) == str(LocalLatest):
                        pr('{}:{}已存在,Done'.format(Organization, Title))
                        LoopFlag = False
                        break
                    else:
                        pass

                    WebUrl = menu[j]
                    No = re.findall(r'\d+', Title)[0]
                    try:
                        DownloadDate = datetime.datetime.now().strftime('%Y.%m.%d')
                    except:
                        DownloadDate = 'None'
                    try:
                        Intro = (
                            psor(DetailSite.text)
                            .xpath('//header/div/span[4]/text()[2]')
                            .get()
                        )
                    except:
                        Intro = 'None'
                    try:
                        WebDate = re.findall(r'\d{4}.\d{2}.\d{2}', Intro)[0]
                    except:
                        WebDate = 'None'
                    try:
                        Name = (
                            psor(DetailSite.text)
                            .xpath(
                                "//div[@class='content']/header/div/span[@class='item item-2']/a/text()"
                            )
                            .get()
                        )
                    except:
                        Name = 'None'
                    MultiThreadArr = []
                    AllSite = (
                        psor(DetailSite.text)
                        .xpath('//div/article/div[1]/ul/a/@href')
                        .getall()[0:-1]
                    )
                    for item in range(len(AllSite)):
                        AllSite[item] = HomeSite + AllSite[item]
                    PictureList = []
                    for k in AllSite:
                        MultiThreadArr.append(
                            threading.Thread(
                                target=GetPictureUrl,
                                args=(
                                    k,
                                    Header,
                                ),
                            )
                        )
                    for item in MultiThreadArr:
                        item.start()
                    for item in MultiThreadArr:
                        item.join()
                    for item in range(len(PictureList)):
                        PictureList[item] = HomeSite[:-1] + PictureList[item]
                    pbar = tqdm.tqdm(
                        total=len(PictureList),
                        leave=False,
                        unit='img',
                        desc=Organization + '-' + re.findall(r'\d+', Title)[0],
                    )
                    MultiThreadArr = []
                    for item in PictureList:
                        MultiThreadArr.append(
                            threading.Thread(
                                target=DownLoadList,
                                args=(
                                    item,
                                    Header['user-agent'],
                                    Organization,
                                    Title,
                                ),
                            )
                        )
                    for item in MultiThreadArr:
                        item.start()
                    for item in MultiThreadArr:
                        item.join()
                    pbar = None
                    info = {}
                    info['Title'] = Title
                    info['WebUrl'] = WebUrl
                    info['Name'] = Name
                    info['No.'] = int(No)
                    info['DownloadDate'] = DownloadDate
                    info['WebDate'] = WebDate
                    info['Intro'] = Intro
                    info['PicturesPath'] = PictureList
                    NameArr.append(Name)
                    shutil.copy(
                        '{}/../json/{}.json'.format(path, Organization),
                        '{}/../json/tmp.json'.format(path),
                    )
                    with open(
                        '{}/../json/tmp.json'.format(path, Organization),
                        'r',
                        encoding='utf8',
                    ) as tmpjson:
                        try:
                            tmpjson = json.load(tmpjson)
                        except:
                            tmpjson = []

                    InfoArr = []
                    InfoArr.append(info)
                    with open(
                        '{}/../json/{}.json'.format(path, Organization),
                        'w',
                        encoding='utf8',
                    ) as PrintInfo:
                        json.dump(
                            InfoArr + tmpjson, PrintInfo, indent=4, ensure_ascii=False
                        )
                    try:

                        threading.Thread(
                            target=Compress_and_Upload,
                            args=(
                                No,
                                Name,
                                Organization,
                                Title,
                            ),
                        ).start()
                    except:
                        pr('failed to upload {}'.format(No))

            else:
                break
    except Exception as Er:
        pr(str(Er))
    finally:
        SortList(Organization)
        with open('{}/../json/name.json'.format(path), 'w', encoding='utf8') as tmpjson:
            json.dump(list(set(NameArr)), tmpjson, ensure_ascii=False, indent=4)


def main():

    for i in Config:
        Header = {
            'user-agent': fake_useragent.UserAgent(
                path='{}/../json/ua.json'.format(path),
            ).random,
            'Connection': 'close',
        }
        res = requests.get(
            url=HomeSite + i, timeout=Timeout, verify=False, headers=Header
        )
        res.encoding = 'utf8'
        Page = re.findall(
            r'\d+',
            psor(res.text).xpath("//div[@class='pagination']/ul/a[last()]/@href").get(),
        )[-1]
        WebLatest = re.findall(
            r'\d+', psor(res.text).xpath('//div/ul/li/a/span').get()
        )[0]
        if os.path.getsize('{}/../json/{}.json'.format(path, i)) != 0:
            with open(
                '{}/../json/{}.json'.format(path, i), 'r', encoding='utf8'
            ) as InsiderData:
                try:
                    LocalLatest = json.load(InsiderData)[0]["No."]
                except:
                    LocalLatest = 'None'
        else:
            LocalLatest = 'None'

        Crawler(i, int(Page), WebLatest, LocalLatest)


if __name__ == '__main__':
    ArchiveName = path + '/../archives/json-{}-{}.7z'.format(
        datetime.datetime.now().strftime('%Y.%m.%d'), RandomString()
    )
    with T7z.SevenZipFile(ArchiveName, 'w', password='MDcxMTI2WHlm') as archive:
        archive.writeall(path + '/../json/', '/jsons/')
    os.system('''bypy upload {} /jsons/'''.format(ArchiveName))
    os.remove(ArchiveName)
    main()
