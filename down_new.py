# -*- coding: utf-8 -*-
"""
Created on Mon Feb 19 11:59:19 2024

@author: xiaoxuan
@E-mail:zhuiqiuzhuyue678@stu.xjtu.edu.cn
@Homepage:https://github.com/littele-xuan
"""
"""
This code is used to easily download files from anonymous github 
You just have to pay attention 
1: Set dir as the local download folder in paerser 
2: Set url to the address of the destination file in paerser 
Note: Both paths need to retain the final '/' 
Thanks: The version provided by https://github.com/kynehc/clone_anonymous_github. This code has been supplemented on this basis, mainly including 
1: You only need a local path code to automatically create a file structure that is the same as the project locally without manual operation 
2: Local download can be performed according to different folder structures

"""
import argparse
import os
import requests
from time import sleep
import concurrent.futures
from json.decoder import JSONDecodeError
import sys

def parse_args():
    parser = argparse.ArgumentParser(description='Clone from the https://anonymous.4open.science')
    parser.add_argument('--dir', type=str, default='C:/Users/admin/Downloads/anonymous/',
                        help='save dir')
    
    parser.add_argument('--url', type=str, default='https://anonymous.4open.science/r/name/',
                        help='target anonymous github link eg., https://anonymous.4open.science/r/840c8c57-3c32-451e-bf12-0e20be300389/')
    parser.add_argument('--max-conns', type=int, default=128,
                        help='max connections number')
    return parser.parse_args()




def dict_parse(dic, pre=None):
    pre = pre[:] if pre else []
    if isinstance(dic, dict):
        for key, value in dic.items():
            if isinstance(value, dict):
                for d in dict_parse(value, pre + [key]):
                    yield d
            else:
                yield pre + [key, value]
    else:
        yield pre + [dic]

def create_local_directory(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def req_url(dl_file, max_retry=5):
    url = dl_file[0]
    save_path = dl_file[1]
    create_local_directory(save_path)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15"
    }
    for i in range(max_retry):
        try:
            r = requests.get(url, headers=headers)
            with open(save_path, "wb") as f:
                f.write(r.content)
            return
        except Exception as e:
            print('file request exception (retry {}): {} - {}'.format(i, e, save_path))
            sleep(0.4)

if __name__ == '__main__':
    args = parse_args()
    assert args.url, '\nPlese specify your target anonymous github link.\nExample: ' \
                     + 'python download.py --url https://anonymous.4open.science/r/840c8c57-3c32-451e-bf12-0e20be300389/'

    url = args.url
    name = url.split('/')[-2]
    max_conns = args.max_conns

    print("[*] Cloning project:", name)

    list_url = "https://anonymous.4open.science/api/repo/" + name + "/files/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15"
    }
    retry_count = 0
    while True:
        try:
            resp = requests.get(url=list_url, headers=headers)
            resp.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx status codes)
            file_list = resp.json()
            break  # Exit the loop if request is successful
        except requests.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                retry_count += 1
                if retry_count > 5:  # Limit the number of retries
                    print("Too many retries. Exiting.")
                    sys.exit(1)
                print("Too many requests. Waiting for a while and then retrying...")
                sleep(60)  # Wait for 60 seconds and then retry
            else:
                print("Failed to fetch file list:", e)
                sys.exit(1)

    print("[*] Downloading files:")

    dl_url = "https://anonymous.4open.science/api/repo/" + name + "/file/"
    files = []
    for file in dict_parse(file_list):
        file_path = os.path.join(*file[-len(file):-2])  # * operator to unpack the arguments out of a list
        file_path = file_path.replace("\\", "/")
        save_path = os.path.join(args.dir, file_path)
        file_url  = dl_url + file_path
        files.append((file_url, save_path))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_conns) as executor:
        future_to_url = (executor.submit(req_url, dl_file) for dl_file in files)
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                future.result()
            except Exception as exc:
                print("An error occurred:", exc)

    print("[*] Files saved to:", args.dir)