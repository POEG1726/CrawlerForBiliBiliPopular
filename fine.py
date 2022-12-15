import datetime
import getopt
import json
import os
import random
import re
import shutil
import string
import sys
import threading
from time import sleep

import fake_useragent
import paramiko
import parsel
import requests
import tqdm
from requests.adapters import HTTPAdapter

requests.packages.urllib3.disable_warnings()
s = requests.Session()
s.mount('http://', HTTPAdapter(max_retries=20))
s.mount('https://', HTTPAdapter(max_retries=20))

global pbar, Config, PictureList, StartPage, writeable, Target, ChangeTarget, Ignore, upload, HomeSite, download  # , Point
upload = True
download = True
ChangeTarget = False
# Point = None
Ignore = True
pr = tqdm.tqdm.write
writeable = True
StartPage = 0
psor = parsel.Selector
path = sys.path[0]
Timeout = None
HomeSite = ''
Lock = threading.Lock()
threadsmax = threading.BoundedSemaphore(15)
PictureList = []
with open(
    '{}/../json/config.json'.format(path),
    'r',
    encoding='utf8',
) as Config:
    Config = json.load(Config)
    HomeSite = Config['HomeSite']
    Config = Config['Organization']


def FrontTask():
    Header = {
        'user-agent': fake_useragent.UserAgent(
            cache_path='{}/../json/ua.json'.format(path),
        ).random,
        'Connection': 'close',
    }
    global HomeSite
    tmp = 'https://www.quanjixiu.top/'
    tmp = requests.get(
        url=tmp,
        timeout=Timeout,
        headers=Header,
        verify=True,
    )
    tmp.encoding = 'utf8'
    tmp = psor(tmp.text).xpath('//td/a[1]/@href').get().lower() + '/'
    if HomeSite != tmp:
        HomeSite = tmp
        with open(
            '{}/../json/config.json'.format(path),
            'r+',
            encoding='utf8',
        ) as tmpjson:
            tmp = json.load(tmpjson)
        tmp['HomeSite'] = HomeSite
        tmp['LatestCheck'] = datetime.datetime.now().strftime('%Y.%m.%d %H:%M')
        with open(
            '{}/../json/config.json'.format(path), 'w', encoding='utf8'
        ) as tmpjson:
            json.dump(tmp, tmpjson)
        return True
    else:
        return False


def Choose(Flag=True, *args) -> list:
    dic = {}
    cfg = Config
    count = 1
    for i in cfg:
        dic[str(count)] = i
        count += 1
    if Flag:
        for key, vue in dic.items():
            print('{}:{}'.format(key, vue))
        choice = input('please type your choice(order):').split(',')
    else:
        choice = args[0].split(',')
    choice = [i for i in choice if i != '']
    tmp = []
    for i in choice:
        tmp.append(dic[i])
    return tmp


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
        '{}/../json/{}.json'.format(path, Organization),
        'r',
        encoding='utf8',
    ) as tmpjson:
        try:
            data = json.load(tmpjson)
        except:
            return
    data = sorted(data, key=lambda r: r['No.'], reverse=True)
    with open(
        '{}/../json/{}.json'.format(path, Organization),
        'w',
        encoding='utf8',
    ) as tmpjson:
        json.dump(data, tmpjson, indent=4, ensure_ascii=False)


def SSHClient():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    hostname = '192.168.2.4'
    port = 22
    username = 'root'
    passwd = '071126Xyf'
    ssh.connect(
        hostname=hostname,
        port=port,
        username=username,
        password=passwd,
    )
    ssh.exec_command('''ln -s src dst''')
    ssh.close()


def Compress_and_Upload(vol, owner, Organization, title):
    # Lock.acquire()
    threadsmax.acquire()
    ArchiveName = (
        path + '/../archives/' + '[' + Organization + ']' + vol + '-' + owner + '.7z'
    )
    os.system(
        '''/nas/code/crawler/script/7zz a -pMDcxMTI2WHlm -r '{}' '/nas/Girls/{}/{}/' >/dev/null 2>&1'''.format(
            ArchiveName, Organization, title
        )
    )
    os.system(
        '''bypy --processes 4 upload {} /photos/{}/ >/dev/null 2>&1'''.format(
            ArchiveName, Organization
        )
    )
    sleep(1)
    os.remove(ArchiveName)
    threadsmax.release()
    # Lock.release()


def GetPictureUrl(DetailSite_Url: str, Header: dict):
    global PictureList
    DetailSite = requests.get(
        url=DetailSite_Url,
        timeout=Timeout,
        verify=True,
        headers=Header,
    )
    DetailSite.encoding = 'utf8'
    Lock.acquire()
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


def Crawler(
    Organization: str,
    Ends: int,
    RemoteLatest: int,
    LocalLatest: int,
):
    global pbar, PictureList
    with open(
        '{}/../json/name.json'.format(path),
        'r',
        encoding='utf8',
    ) as tmpjson:
        try:
            NameList = json.load(tmpjson)
        except:
            NameList = []
    try:
        if ChangeTarget == True:
            pr(
                'The latest in json is {},but have -t option with {}'.format(
                    LocalLatest, Target
                )
            )
            LocalLatest = Target
        if LocalLatest == RemoteLatest:
            pr(
                '[{}] {}:网站未更新'.format(
                    datetime.datetime.now().strftime('%H:%M:%S'), Organization
                )
            )
            return
        else:
            pr(
                '[{}] {}:网站已更新  [{}->{}]'.format(
                    datetime.datetime.now().strftime('%H:%M:%S'),
                    Organization,
                    RemoteLatest,
                    LocalLatest,
                )
            )
        LoopFlag = True
        for i in range(
            StartPage,
            Ends,
        ):
            if LoopFlag == True:
                if i == 0:
                    InitialSite = HomeSite + Organization
                else:
                    InitialSite = (
                        HomeSite + Organization + '/page_{}.html'.format(i + 1)
                    )
                Header = {
                    'user-agent': fake_useragent.UserAgent(
                        cache_path='{}/../json/ua.json'.format(path),
                    ).random,
                    'Connection': 'close',
                }
                res = requests.get(
                    url=InitialSite,
                    timeout=Timeout,
                    verify=True,
                    headers=Header,
                )
                res.encoding = 'utf8'
                menu = (
                    psor(res.text)
                    .xpath("//div[@class='related_posts']/ul//li/a/@href")
                    .getall()
                )
                for item in range(len(menu)):
                    menu[item] = HomeSite + menu[item][1:]
                with open(
                    '{}/../json/{}.json'.format(path, Organization),
                    'r',
                    encoding='utf8',
                ) as tmpjson:
                    try:
                        tmpjson = json.load(tmpjson)
                    except:
                        tmpjson = []
                isexist_no = []
                for i in range(len(tmpjson)):
                    isexist_no.append(tmpjson[i]['No.'])
                for j in range(len(menu)):
                    DetailSite = requests.get(
                        url=menu[j],
                        timeout=Timeout,
                        verify=True,
                        headers=Header,
                    )
                    DetailSite.encoding = 'utf8'
                    Title = str(psor(DetailSite.text).xpath("//header/h1/text()").get())
                    if not Title:
                        DetailSite = requests.get(
                            url=menu[j],
                            timeout=Timeout,
                            verify=True,
                            headers=Header,
                        )
                        DetailSite.encoding = 'utf8'
                        Title = str(
                            psor(DetailSite.text).xpath("//header/h1/text()").get()
                        )
                    # if Point and Point < int(re.findall(r'\d+', Title)[0]):
                    #     continue
                    if Ignore and int(re.findall(r'\d+', Title)[0]) in isexist_no:
                        if int(re.findall(r'\d+', Title)[0]) == LocalLatest:
                            pr(
                                '[{}] {}:{}已存在,Done'.format(
                                    datetime.datetime.now().strftime('%H:%M:%S'),
                                    Organization,
                                    int(re.findall(r'\d+', Title)[0]),
                                )
                            )
                            return
                        else:
                            pr(
                                '{}:{} already existed'.format(
                                    Organization, int(re.findall(r'\d+', Title)[0])
                                )
                            )
                            continue
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
                        '[{}] {}:当前:{} target={}'.format(
                            datetime.datetime.now().strftime('%H:%M:%S'),
                            Organization,
                            int(re.findall(r'\d+', Title)[0]),
                            LocalLatest,
                        )
                    )
                    if int(re.findall(r'\d+', Title)[0]) == LocalLatest:
                        pr(
                            '[{}] {}:{}已存在,Done'.format(
                                datetime.datetime.now().strftime('%H:%M:%S'),
                                Organization,
                                int(re.findall(r'\d+', Title)[0]),
                            )
                        )
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
                    MultiThreadList = []
                    AllSite = (
                        psor(DetailSite.text)
                        .xpath('//div/article/div[1]/ul/a/@href')
                        .getall()[0:-1]
                    )
                    for item in range(len(AllSite)):
                        AllSite[item] = HomeSite + AllSite[item]
                    PictureList = []
                    for k in AllSite:
                        MultiThreadList.append(
                            threading.Thread(
                                target=GetPictureUrl,
                                args=(
                                    k,
                                    Header,
                                ),
                                name=f'{Organization}.{No}.GetPictureUrl',
                            )
                        )
                    for item in MultiThreadList:
                        item.start()
                    for item in MultiThreadList:
                        item.join()
                    for item in range(len(PictureList)):
                        PictureList[item] = HomeSite[:-1] + PictureList[item]
                    pbar = tqdm.tqdm(
                        total=len(PictureList),
                        leave=False,
                        unit='img',
                        desc=Organization
                        + '-'
                        + str(int(re.findall(r'\d+', Title)[0])),
                    )
                    MultiThreadList = []
                    if download:
                        for item in PictureList:
                            MultiThreadList.append(
                                threading.Thread(
                                    target=DownLoadList,
                                    args=(
                                        item,
                                        Header['user-agent'],
                                        Organization,
                                        Title,
                                    ),
                                    name=f'{Organization}.{No}.DownLoadList',
                                )
                            )
                        for item in MultiThreadList:
                            item.start()
                        for item in MultiThreadList:
                            item.join()
                    pbar = None
                    info = {}
                    info['Title'] = Title
                    info['WebUrl'] = WebUrl
                    info['Inpage'] = int(i + 1)
                    info['Name'] = Name
                    info['No.'] = int(No)
                    info['DownloadDate'] = DownloadDate
                    info['WebDate'] = WebDate
                    info['Intro'] = Intro
                    info['Lenght'] = len(PictureList)
                    info['PicturesPath'] = PictureList
                    NameList.append(Name)
                    if writeable:
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

                        InfoList = []
                        InfoList.append(info)
                        with open(
                            '{}/../json/{}.json'.format(path, Organization),
                            'w',
                            encoding='utf8',
                        ) as PrintInfo:
                            json.dump(
                                InfoList + tmpjson,
                                PrintInfo,
                                indent=4,
                                ensure_ascii=False,
                            )
                    if upload:
                        try:
                            threading.Thread(
                                target=Compress_and_Upload,
                                args=(
                                    No,
                                    Name,
                                    Organization,
                                    Title,
                                ),
                                name=f'{Organization}.{No}.Compress&Upload',
                            ).start()
                        except:
                            pr('{}:failed to upload {}'.format(Organization, No))

            else:
                break
    except Exception as Er:
        pr(str(Er))
    finally:
        if writeable:
            SortList(Organization)
            with open(
                '{}/../json/name.json'.format(path), 'w', encoding='utf8'
            ) as tmpjson:
                json.dump(list(set(NameList)), tmpjson, ensure_ascii=False, indent=4)


# def main(point):
def main():
    with open(
        '{}/../json/config.json'.format(path),
        'r',
        encoding='utf8',
    ) as tmp:
        tmp = json.load(tmp)
    tmp = tmp['LatestCheck']
    tmp = datetime.datetime.strptime(tmp, '%Y.%m.%d %H:%M')
    tmp = datetime.datetime.now() - tmp
    if tmp.days > 2:
        pr('自动运行FrontTask')
        if FrontTask():
            pr('已更改HomeSite ', end='')
        else:
            pr('HomeSite未更改 ', end='')
    pr(f'当前HomeSite [{HomeSite}]')
    for i in Config:
        if writeable:
            SortList(i)
        Header = {
            'user-agent': fake_useragent.UserAgent(
                cache_path='{}/../json/ua.json'.format(path),
            ).random,
            'Connection': 'close',
        }

        res = requests.get(
            url=HomeSite + i, timeout=Timeout, verify=True, headers=Header
        )
        res.encoding = 'utf8'
        Page = int(
            re.findall(
                r'\d+',
                psor(res.text)
                .xpath("//div[@class='pagination']/ul/a[last()]/@href")
                .get(),
            )[-1]
        )
        RemoteLatest = int(
            re.findall(r'\d+', psor(res.text).xpath('//div/ul/li/a/span').get())[0]
        )
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
        # if Point != None:
        #     Mo = point % 20
        #     if RemoteLatest -
        Crawler(i, Page, RemoteLatest, LocalLatest)


if __name__ == '__main__':
    opts, args = getopt.getopt(
        args=sys.argv[1:],
        # shortopts='-h-s:-m:-t:-i-u-c-p:',
        shortopts='-h-s:-m:-t:-i-u-c-o-d',
        longopts=[
            'help',
            'startpage=',
            'mode=',
            'target=',
            'ignore',
            'upload',
            'check',
            'organization',
            'download'
            # 'point=',
        ],
    )
    if '-s' in sys.argv[1:] and '-p' in sys.argv[1:]:
        raise TypeError("-s option cannot use with -p")
    info = ''
    for opt_name, opt_value in opts:
        if opt_name in ('-h', '--help'):
            pr(
                '''
Tips:  U best take [-m:r]/-p option with -t option
       -s option cannot use with -p
[-h/--help]:show this info
[-s/--startpage (page)]:set the page that the crawler start getting
[-m/--mode (r/w)]:set crawler write json files mode,including writeable,readonly single-download and multi-download
[-t/--target (subject)]:set the subject that crawler stop getting
[-i/--ignore]:disable the module that ignores the subject that already exists,it could cause json content is repeated
[-u/--upload]:disable the module that uploads file to BaiDu netdisk,including .json and img
[-c/--check]:enable check domain's usability
[-o/--organization]:choose Organizations,you can input args in the end(args[0])
[-d/--download]:disable the download module
               '''
                # [-p/--point ()] set the subject that crawler starts getting
            )
            exit()
        if opt_name in ('-s', '--startpage'):
            try:
                StartPage = int(opt_value) - 1
            except:
                raise TypeError('option [{}] can only be [int] type'.format(opt_name))
            info = info + '将从第{}页开始,'.format(StartPage + 1)

        if opt_name in ('-m', '--mode'):
            ModeList = ['r', 'w', 's', 'm']
            if opt_value not in ModeList:
                raise TypeError(
                    'option [{}] can only choose in [r/w/s/m]'.format(opt_name)
                )
            info = info + '选择[{}]模式,'.format(opt_value)
            if opt_value == 'r':
                writeable = False
            if opt_value == 'w':
                writeable == True

        if opt_name in ('-t', '--target'):
            try:
                Target = int(opt_value)
            except:
                raise TypeError('option [{}] can only be [int] type'.format(opt_name))
            info = info + '将在第{}期结束,'.format(opt_value)
            ChangeTarget = True

        if opt_name in ('-i', '--ignore'):
            info = info + '不忽略已存在subject-可能造成json重复'
            Ignore = False

        if opt_name in ('-u', '--upload'):
            info = info + '关闭百度网盘同步,'
            upload = False

        if opt_name in ('-c', '--check'):
            info = info + '打开网站可用性校验,'
            FrontTask()

        if opt_name in ('-o', '--organization'):
            if args:
                Config = Choose(False, args[0])
            else:
                Config = Choose()
            info = info + '选择了{},'.format(Config)

        if opt_name in ('-d', '--download'):
            download = False
            info = info + '关闭wget下载,'
        # if opt_name in ('-p', '--point'):
        #     try:
        #         Point = int(opt_value)
        #     except:
        #         raise TypeError('option [{}] can only be [int] type'.format(opt_name))
        #     info = info + '将从第{}期开始'.format(Point)

    pr(info[:-1])
    starttime = datetime.datetime.now()
    if upload:
        ArchiveName = path + '/../archives/json-{}-{}.7z'.format(
            datetime.datetime.now().strftime('%Y.%m.%d'), RandomString()
        )
        os.system(
            f'''/nas/code/crawler/script/7zz a -pMDcxMTI2WHlm -r '{ArchiveName}' '/nas/code/crawler/json/' >/dev/null 2>&1'''
        )
        # with T7z.SevenZipFile(ArchiveName, 'w', password='MDcxMTI2WHlm') as archive:
        #     archive.writeall(path + '/../json/', '/jsons/')
        os.system('''bypy upload {} /jsons/'''.format(ArchiveName))
        os.remove(ArchiveName)

    # main(Point)
    main()

    endtime = datetime.datetime.now()
    pr('--Spend [{}]'.format(str(endtime - starttime).split('.')[0]))
    pr('-----Start time is:{}'.format(str(starttime).split('.')[0]))
    pr('-----End time is:{}'.format(str(endtime).split('.')[0]))
