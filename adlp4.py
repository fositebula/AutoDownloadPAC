#!/usr/bin/env python
#-*- coding:utf-8 -*-
#-----------------------------------------------------
#A demo fot Auto download daily pac

import requests
from bs4 import BeautifulSoup
import os
import time
import json
from requests.exceptions import ConnectionError
import traceback
import multiprocessing

WHITE_URL = 'http://10.0.70.54:8080/tjxt/index/get_white_list_pac_info'
STORAGE_FILE = 'urls_infos'

def get_urls():
    r = requests.get(WHITE_URL)
    sorc_urls = r.json()['data']
    def md_urls(url):
        if 'view' in url:
            return {'/'.join(url.split('/')[:8])+'/lastSuccessfulBuild/artifact/': {'url': url}}
        return {'/'.join(url.split('/')[:6])+'/lastSuccessfulBuild/artifact/': {'url': url}}
    urls_d = {}
    for url in sorc_urls:
        urls_d.update(md_urls(url))
    return urls_d

def get_verify_urlid(urls):
    for url in urls.keys():
        r = requests.get(url)
        if r.status_code != 200:
            return url
        bs = BeautifulSoup(r.content, 'lxml')
        urls[url]['id'] = bs.select('#main-panel h1')[0].get_text().split('#')[-1]
    return urls


def get_verify_id(url):
    r = requests.get(url)
    if r.status_code != 200:
        return 0
    bs = BeautifulSoup(r.content, 'lxml')
    return bs.select('#main-panel h1')[0].get_text().split('#')[-1]

def download_or_not(urls):
    with open(STORAGE_FILE, 'r+') as f:
        urls = json.load(f)
        verifyids = []
        for url in urls.keys():
            try:
                verifyid = get_verify_id(url)
            except ConnectionError:
                traceback.print_exc()
                time.sleep(1)
                continue
            if verifyid == urls[url]['id']:
                continue
            urls[url]['id'] = verifyid
            print verifyid
            #TODO:下载
            verifyids.append((urls[url]['url'], verifyid))

        f.seek(0)
        f.truncate()
        json.dump(urls, f)
    return verifyids


def download_pac(url, verifyid):
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print 'get url fail: %d'%r.status_code
        return 'get url fail: %d'%r.status_code
    url_s = url.split('/')
    if 'view' in url:
        branch = url_s[7]
        project = url_s[12]
        pac = url_s[-1]
    else:
        branch = url_s[5]
        project = url_s[9]
        pac = url_s[-1]

    if not os.path.exists(branch):
        os.mkdir(branch)
        os.mkdir(os.path.join(branch, project))
        os.mkdir(os.path.join(branch, project, verifyid))
    else:
        if not os.path.exists(os.path.join(branch, project)):
            os.mkdir(os.path.join(branch, project))
            os.mkdir(os.path.join(branch, project, verifyid))
        elif not os.path.exists(os.path.join(branch, project, verifyid)):
            os.mkdir(os.path.join(branch, project, verifyid))
    with open(os.path.join(branch, project, verifyid, pac), 'w') as f:
        for line in r.iter_lines():
            f.write(line)


def init_json():
    urls = get_urls()

    url_id = get_verify_urlid(urls)
    print url_id
    with open('urls_infos.json', 'r+') as f:
        json.dump(url_id, f)
        f.flush()

if __name__ == '__main__':

    urls = get_urls()

    url_id = get_verify_urlid(urls)
    print url_id
    with open(STORAGE_FILE, 'r+') as f:
        tof = json.dump(url_id, f)
        f.flush()
    process = []
    while True:
        verifyids = download_or_not(url_id)
        for url_verifyid in verifyids:
            p = multiprocessing.Process(target=download_pac, args=url_verifyid, name='download_pac')
            process.append(p)
            p.start()
            print p.pid
        print process
        for pro in process:
            pro.join()
        time.sleep(300)
    # url = 'http://10.0.1.163:8080/jenkins/job/sprdroid4.4_sfphone_17f_rls1/lastBuild/artifact/Images/sp9820e_2h10_native-userdebug-native/sp9820e_2h10_native-userdebug-native_MOCER5_2H10_UNCACHE_SIGNE.pac.gz'
    # verifyid = '214'
    # download_pac(url, verifyid)


