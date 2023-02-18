# -*- coding: utf-8 -*- #
# File Name:        main.py
# Author:           POEG1726
# For Domain:       https://www.xiuren01.xyz/XiuRen/

import datetime
import getopt
import json
import os
import random
import re
import shutil
import sys
import threading
import platform
from time import sleep
import json
import fake_useragent
import parsel
import requests
import tqdm
from requests.adapters import HTTPAdapter
import concurrent.futures

requests.packages.urllib3.disable_warnings()
s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=10))
s.mount('https://', HTTPAdapter(max_retries=10))
HomeSite = 'https://www.xiuren01.xyz/'
domain = re.findall(r'(?<=://)\w+\.\w+', HomeSite)[0]
Root = os.path.join(sys.path[0], '..')
psor = parsel.Selector
os_name = platform.system()
if os_name == 'Windows':
    NAS_Path = 'Z:'
else:
    NAS_Path = '/nas'


def Preload():
    with open(f'{Root}/config.json', 'r', encoding='utf8') as Config_File:
        org = json.load(Config_File)
    for item in org:
        # asyncio.run(main(item))
        result = main(item)
        if result[0] == 2:
            print(f'{item}出现错误,已经记录在log中,详情见log')


def main(Organization: str):
    MainSite = os.path.join(HomeSite, Organization)
    with open(f'{Root}/json/XiuRen.json', 'r', encoding='utf8') as data:
        data = json.load(data)
    data: list
    Header = {
        'user-agent': fake_useragent.UserAgent(
            cache_path='{}/json/ua.json'.format(Root),
        ).random,
        'Connection': 'close',
        'Host': domain,
    }
    Page = requests.get(url=MainSite, headers=Header, timeout=None)
    Page.encoding = 'utf8'
    Page = Page.text
    Latest_Serial = int(
        re.findall(
            r'\d+',
            psor(Page)
            .xpath('/html/body/div[3]/div/div/ul/li[1]/div/div[1]/text()')
            .get(),
        )[-1]
    )
    if Latest_Serial == data[0]['Serial']:
        return (0, '网站未更新')
    Total_Pages = int(
        re.findall(
            r'\d+',
            psor(Page).xpath('/html/body/div[3]/div/div/div[2]/a[9]/@href').get(),
        )[-1]
    )
    Loop_Flag = True
    for i in range(Total_Pages):
        if Loop_Flag == True:
            if i == 0:
                url = MainSite
            else:
                url = MainSite + f'/index{i+1}.html'
            Page = requests.get(url=url, headers=Header, timeout=None)
            Page.encoding = 'utf8'
            Page = Page.text
            UrlList = psor(Page).xpath('//li[@class="i_list list_n2"]/a/@href').getall()
            UrlList = [HomeSite[:-1] + x for x in UrlList]
            for j in range(len(UrlList)):
                Details = {}
                Page = requests.get(url=UrlList[j], headers=Header, timeout=None)
                Page.encoding = 'utf8'
                Page = Page.text
                Details['Title'] = re.sub(
                    r'([a-zA-Z]*\.)(\d+)([_])',
                    r'第\2期',
                    str(
                        psor(Page)
                        .xpath('//p/img/@alt')
                        .getall()[0]
                        .replace('秀人集.com_', '')
                        .replace('IMISS', 'Imiss')
                        .replace('XINGYAN', 'XingYan')
                    ),
                )
                Details['Serial'] = int(re.match(r"第[\d+]期", Details['Title']).group[0])
                if Details['Serial'] == data[0]['Serial']:
                    Loop_Flag = False
                    break
                Details['Intro'] = (
                    psor(Page)
                    .xpath('/html/body/div[3]/div/div/div[1]/div/text()')
                    .get()
                )
                Details['Role'] = (
                    psor(Page)
                    .xpath('/html/body/div[3]/div/div/div[2]/div/a[3]/span/text()')
                    .get()
                )
                Details['WebUrl'] = j
                Details['UpdateTime'] = re.findall(
                    r'\d{4}.\d{2}.\d{2}', Details['Intro']
                )[0]
                Details['DownloadTime'] = datetime.datetime.now().strftime(
                    r'%Y.%m.%d %H:%M:%S'
                )

                Detail_Urls = (
                    psor(Page)
                    .xpath('/html/body/div[3]/div/div/div[4]/div/div/a/@href')
                    .getall()[:-1]
                )
                Detail_Urls = [HomeSite[:-1] + x for x in Detail_Urls]
                Second_Header = {
                    'user-agent': fake_useragent.UserAgent(
                        cache_path='{}/json/ua.json'.format(Root),
                    ).random,
                    'Connection': 'close',
                    'Host': domain,
                }
                with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                    futures = [
                        executor.submit(GetPictureUrl, value, Second_Header)
                        for value in Detail_Urls
                    ]
                    results = [future.result() for future in futures]
                PictureUrls = []
                [PictureUrls.extend(x) for x in results]
                Details['Length'] = len(PictureUrls)
                Details['PictureUrls'] = PictureUrls
                sorted(Details.items(), key=lambda x: x[0], reverse=False)
                Second_Header = {
                    'user-agent': fake_useragent.UserAgent(
                        cache_path='{}/json/ua.json'.format(Root),
                    ).random,
                    'Connection': 'close',
                    'Host': domain,
                }
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [
                        executor.submit(
                            Donwload, x, Organization, Details['Title'], Second_Header
                        )
                        for x in PictureUrls
                    ]
                    list(
                        tqdm.tqdm(
                            concurrent.futures.as_completed(futures),
                            total=Details['Length'],
                            leave=False,
                            unit='img',
                            desc=f'[{Organization}] {Details["Role"]}',
                        )
                    )
                data.append(Details)
                with open(
                    os.path.join(Root, f'json/{Organization}.json'),
                    'r',
                    encoding='utf8',
                ) as f:
                    json.dump(data, f, ensure_ascii=False)
        else:
            with open(
                os.path.join(Root, f'json/{Organization}.json'), 'r', encoding='utf8'
            ) as f:
                data = json.load(f)
            with open(
                os.path.join(Root, f'json/{Organization}.json'), 'r', encoding='utf8'
            ) as f:
                json.dump(
                    sorted(data, key=lambda x: x['serial'], reverse=True),
                    f,
                    ensure_ascii=False,
                )
            break
    return (0, '运行结束')


def GetPictureUrl(PageUrl: str, Header: dict) -> list:
    Page = requests.get(url=PageUrl, headers=Header, timeout=None)
    Page.encoding = 'utf8'
    Page = Page.text
    Url_Arr = psor(Page).xpath('//p/img/@src').getall()
    Url_Arr = [HomeSite[:-1] + i for i in Url_Arr]
    return Url_Arr


def Donwload(PictureUrl: str, Org: str, Title: str, Header: dict):
    os.system(
        f'''{os.path.join(Root,'Programes/lwget.exe')} -q -nc -P '{NAS_Path}/Girls/Pictures/{Org}/{Title}' '{PictureUrl}' -U "{Header['user-agent']}" –tries=5 --method GET –tries=5'''
    )


def SortList(Organization):
    with open(
        '{}/../json/{}.json'.format(Root, Organization),
        'r',
        encoding='utf8',
    ) as tmpjson:
        try:
            data = json.load(tmpjson)
        except:
            return
    data = sorted(data, key=lambda r: r['Serial'], reverse=True)
    with open(
        '{}/../json/{}.json'.format(Root, Organization),
        'w',
        encoding='utf8',
    ) as tmpjson:
        json.dump(data, tmpjson, indent=4, ensure_ascii=False)


def MakeArchive(Org: str, Role: str, Serial: str, Title: str):
    os.system(
        f'''{os.path.join(Root,'programe/7z.exe')} a -pMDgwNDE2V3pxaWlp -r {os.path.join(Root,f'Archive/{Org}.{Serial}.{Role}.zip')} {os.path.join(NAS_Path,f'./Girls/Pictures/{Title}')}'''
    )


if __name__ == '__main__':
    Preload()
