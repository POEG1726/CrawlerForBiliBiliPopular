import PCSAPI
from PCSAPI.api import fileupload_api
from PCSAPI.api import userinfo_api
import json
import os
import hashlib
import Plugins
import tkinter as tk
from tkinter import filedialog
import fake_useragent
from math import ceil
import threading
from pprint import pprint

Header = {
    'user-agent': fake_useragent.UserAgent(cache_path='./ua.json').random,
}
MB4 = 4194304


def PartFile(path: str):
    f = open(path, 'rb')

    def read(Seq: int):
        data = f.read(MB4)
        if not data:
            return
        with open(f'../output/tmp/{Seq}', 'wb') as tmp:
            tmp.write(data)

    threadarr = []
    for i in range(ceil(os.path.getsize(path) / MB4)):
        threadarr.append(threading.Thread(target=read, args=(i,)))
    for i in threadarr:
        i.start()
    for i in threadarr:
        i.join()

    f.close()


def precreate(
    Path: str,
    access_token: str,
    RemotePath: str,
    rtype=1,
    autoinit=1,
) -> list:
    """
    precreate
    """
    isdir = int(not os.path.isfile(Path))
    if isdir == 1:
        raise ValueError('Cannot upload a dir')
    block_list = []
    with PCSAPI.ApiClient() as api_client:
        api_instance = fileupload_api.FileuploadApi(api_client)
        size = os.path.getsize(Path)
        print(f"文件大小:{Plugins.get_size_format(size)}")
        if size < MB4:
            with open(Path, 'rb') as f:
                data = f.read(size)
            data = hashlib.md5(data).hexdigest().lower()
            block_list.append(data)
        else:
            with open(Path, 'rb') as f:
                while True:
                    data = f.read(MB4)
                    if not data:
                        break
                    block_list.append(hashlib.md5(data).hexdigest().lower())
        block_list = json.dumps(block_list)
        # example passing only required values which don't have defaults set
        # and optional values
        api_response = api_instance.xpanfileprecreate(
            access_token,
            RemotePath,
            isdir,
            size,
            autoinit,
            block_list,
            rtype=rtype,
        )
        content = [api_response, block_list]
        # pprint(content)
        return content


def upload(
    access_token: str,
    Seq: str,
    RemotePath: str,
    uploadid: str,
    Path: str,
    Type='tmpfile',
) -> dict:
    # Enter a context with an instance of the API client
    with PCSAPI.ApiClient() as api_client:
        # Create an instance of the API class
        api_instance = fileupload_api.FileuploadApi(api_client)
        file = open(Path, 'rb')
        # example passing only required values which don't have defaults set
        # and optional values
        # try:
        api_response = api_instance.pcssuperfile2(
            access_token,
            Seq,
            RemotePath,
            uploadid,
            Type,
            file=file,
        )
        # pprint(api_response)
        return api_response
        # except PCSAPI.ApiException as e:
        #     print(f'Exception when calling FileuploadApi->pcssuperfile2: {e}\n')


def create(
    access_token: str,
    RemotePath: str,
    size: int,
    uploadid: str,
    block_list: str,
    isdir=0,
):
    """
    create
    """
    # Enter a context with an instance of the API client
    with PCSAPI.ApiClient() as api_client:
        # Create an instance of the API class
        api_instance = fileupload_api.FileuploadApi(api_client)
        # example passing only required values which don't have defaults set
        # and optional values
        try:
            api_response = api_instance.xpanfilecreate(
                access_token, RemotePath, isdir, size, uploadid, block_list, rtype=1
            )
            print(api_response)
        except PCSAPI.ApiException as e:
            print(f"Exception when calling FileuploadApi->xpanfilecreate: {e}")


def user_info(access_token):
    """
    user_info demo
    """
    # Enter a context with an instance of the API client
    with PCSAPI.ApiClient() as api_client:
        # Create an instance of the API class
        api_instance = userinfo_api.UserinfoApi(api_client)

        # example passing only required values which don't have defaults set
        try:
            api_response = api_instance.xpannasuinfo(access_token)
            print(api_response)
        except PCSAPI.ApiException as e:
            print("Exception when calling UserinfoApi->xpannasuinfo: %s\n" % e)


def main():
    try:
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename()
    except:
        path = input('无法弹出windows选择框,请手动输入:'.replace('\n', ''))
    token = '121.d6e5efa1f849823970bc56846ad94072.YnrlaQ3NQtmrpzLkr5nXYUOZaout_3DGLZ8cIRY.RK-XpQ'
    if path:
        RemotePath = os.path.join(
            os.path.join(
                "/apps/GetInfo/", input('输入文件在网盘的位置(/apps/GetInfo/):'.replace('\n', ''))
            ),
            str(os.path.split(path)[-1]),
        )
        pprint(RemotePath)
        Result_pre = precreate(Path=path, access_token=token, RemotePath=RemotePath)
    else:
        raise ValueError('You must choose a file')
    PartFile(path)
    count = 0
    ThreadArr = []
    for root, dirs, files in os.walk(top='../output/tmp', topdown=True):
        for name in files:
            Looppath = os.path.join(root, name)
            ThreadArr.append(
                threading.Thread(
                    target=upload,
                    args=(
                        token,
                        str(count),
                        RemotePath,
                        Result_pre[0]['uploadid'],
                        Looppath,
                    ),
                    name=str(count),
                )
            )
            # upload(token, str(count), RemotePath, Result_pre['uploadid'], path)
            count += 1
    ThreadArr[0].start()
    ThreadArr[0].join()
    for i in ThreadArr[1:]:
        i.start()
    for i in ThreadArr:
        i.join()
    create(
        access_token=token,
        RemotePath=RemotePath,
        size=os.path.getsize(path),
        uploadid=Result_pre[0]['uploadid'],
        block_list=Result_pre[1],
    )


if __name__ == '__main__':
    main()
