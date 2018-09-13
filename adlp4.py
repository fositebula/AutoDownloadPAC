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
import subprocess

COUNT_EX = 0
WHITE_URL = 'http://10.0.70.54:8080/tjxt/index/get_white_list_pac_info'
STORAGE_FILE = 'urls_infos.json'
DOWLOAD_LAVA = ''

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
    global COUNT_EX
    with open(STORAGE_FILE, 'r+') as f:
        urls = json.load(f)
        verifyids = []
        for url in urls.keys():
            try:
                verifyid = get_verify_id(url)
            except ConnectionError:
                traceback.print_exc()
                COUNT_EX += 1
                print COUNT_EX
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
    r = requests.get(url.replace('lastBuild', verifyid), stream=True)
    if r.status_code != 200:
        print 'get url fail: %d %s'%(r.status_code, url)
        return 'get url fail: %d'%r.status_code
    url_s = url.split('/')
    if 'view' in url:
        branch = url_s[7]
    else:
        branch = url_s[5]

    project_i = url_s.index('Images') + 1
    project = url_s[project_i]
    pac = url_s[-1]

    if not os.path.exists(DOWLOAD_LAVA+branch):
        os.mkdir(DOWLOAD_LAVA+branch)
        os.mkdir(os.path.join(DOWLOAD_LAVA, branch, project))
        os.mkdir(os.path.join(DOWLOAD_LAVA, branch, project, verifyid))
    else:
        if not os.path.exists(os.path.join(DOWLOAD_LAVA, branch, project)):
            os.mkdir(os.path.join(DOWLOAD_LAVA, branch, project))
            os.mkdir(os.path.join(DOWLOAD_LAVA, branch, project, verifyid))
        elif not os.path.exists(os.path.join(DOWLOAD_LAVA, branch, project, verifyid)):
            os.mkdir(os.path.join(DOWLOAD_LAVA, branch, project, verifyid))
    dl_p = os.path.join(DOWLOAD_LAVA, branch, project, verifyid, pac)
    with open(dl_p, 'w') as f:
        for line in r.iter_lines():
            f.write(line)

    request_squrd(dl_p, url, verifyid)

def init():
    urls = get_urls()

    url_id = get_verify_urlid(urls)
    print url_id
    with open('urls_infos.json', 'r+') as f:
        json.dump(url_id, f)
        f.flush()
    return url_id

def request_squrd(download_path, daily_url, dailyid):
    try:
        dtl = requests.get('http://10.0.70.128:8000/submitinfos/infos/list_pac_urls_j/').json()
        print dtl
        device_type = dtl.get(daily_url)
        if not device_type:
            print 'Not in white list!', daily_url
            return
        dp = 'http://worker05:8080/'+download_path
        url_s = daily_url.split('/')
        if 'view' in daily_url:
            branch = url_s[7]
        else:
            branch = url_s[5]

        project_i = url_s.index('Images') + 1
        project = url_s[project_i]

        b_num = branch+"_"+project+str(dailyid)
        y_template = os.path.join('template', device_type+'.yaml')
        cmd = """python submit_for_testing.py \
              --device-type {LAVA_DEVICE_TYPE} \
              --build-number  {build_number}\
              --lava-server {LAVA_SERVER} \
              --qa-server {QA_SERVER} \
              --qa-server-team lkft \
              --qa-server-project {QA_SERVER_PROJECT} \
              --test-plan {yaml} \
              --img-path {DOWNLOAD_URL} \
              --change-id {changeid} \
              --vts-url {VTS_URL} \
              --submitter {SUBMIT_USER_NAME} \
              --qa-token 13194653496cba5209fd1187e37adb5c0260f904"""\
            .format(LAVA_DEVICE_TYPE=device_type,
                    build_number=b_num,
                    LAVA_SERVER='sprd_lava_01',
                    QA_SERVER='http://10.0.70.105:8000',
                    QA_SERVER_PROJECT='remote-lab-demo',
                    yaml=y_template,
                    DOWNLOAD_URL=dp,
                    changeid='0',
                    VTS_URL='0',
                    SUBMIT_USER_NAME='pac_dloader',
                    )

        print cmd
        os.system(cmd)
    except:
        traceback.print_exc()


if __name__ == '__main__':

    url_id = init()
    # urls = get_urls()
    #
    # url_id = get_verify_urlid(urls)
    # print url_id
    # with open(STORAGE_FILE, 'r+') as f:
    #     tof = json.dump(url_id, f)
    #     f.flush()
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
            if not pro.is_alive():
                process.remove(pro)
        print 'sleep'
        time.sleep(30)
    # url = 'http://10.0.1.163:8080/jenkins/job/sprdroid4.4_sfphone_17f_rls1/lastBuild/artifact/Images/sp9820e_2h10_native-userdebug-native/sp9820e_2h10_native-userdebug-native_MOCER5_2H10_UNCACHE_SIGNE.pac.gz'
    # verifyid = '214'
    # download_pac(url, verifyid)


