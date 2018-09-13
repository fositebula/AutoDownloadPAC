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
# import subprocess

COUNT_EX = 0
WHITE_URL = 'http://10.0.70.54:8080/tjxt/index/get_white_list_pac_info'
STORAGE_FILE = 'urls_infos.json'
DOWLOAD_LAVA = ''

def init():
    r = requests.get(WHITE_URL)
    urls_d = {}
    sorc_urls = r.json()['data']
    print sorc_urls
    for url in sorc_urls:
        fid = get_daily_id(url)
        print fid
        sid = checkid(url, fid)
        print sid
        urls_d[url] = {'dailyid': sid}
    return urls_d


def checkid(url, id):
    while True:
        r2 = requests.head(url.replace('lastBuild', id))
        if r2.status_code != 200:
            id = str(int(id) - 1)
            continue
        return id

def get_daily_id(url):
    id_url = url.split('lastBuild')[0]+'/lastBuild'
    print id_url
    r = requests.get(id_url)
    bs = BeautifulSoup(r.content, 'lxml')
    id = bs.select('#main-panel h1')[0].get_text().split('#')[-1].split(' ')[0].strip()
    return id

def download_or_not(urlsid):
    global COUNT_EX

    urls = urlsid
    dailyids = []
    for url in urls.keys():
        try:
            dailyid = get_daily_id(url)
            sdailyid = checkid(url, dailyid)
            if urlsid[url]['dailyid'] == sdailyid:
                continue
        except ConnectionError:
            traceback.print_exc()
            COUNT_EX += 1
            print COUNT_EX
            time.sleep(1)
            continue
        urls[url]['dailyid'] = sdailyid
        print urls
        print dailyid
        #TODO:下载
        dailyids.append((url, sdailyid))

    return dailyids

def download_pac(url, verifyid):
    r = requests.get(url.replace('lastBuild', verifyid), stream=True)
    if r.status_code != 200:
        print 'get url fail: %d %s'%(r.status_code, url.replace('lastBuild', verifyid))
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

    urls_id = init()
    with open(STORAGE_FILE, 'r+') as f:
        json.dump(urls_id, f)
    process = []
    while True:
        with open(STORAGE_FILE, 'r+') as f:
            urls_id = json.load(f)
        daily_urls_id = download_or_not(urls_id)
        with open(STORAGE_FILE, 'r+') as f:
            json.dump(urls_id, f)
        print 'daily_urls_id: ',daily_urls_id
        for daily_url_id in daily_urls_id:
            p = multiprocessing.Process(target=download_pac, args=daily_url_id, name='download_pac')
            process.append(p)
            p.start()
            print 'download_pac PID: ', p.pid
        for pro in process:
            print 'process pid: ', pro.pid
            if not pro.is_alive():
                process.remove(pro)
        print 'sleep'
        time.sleep(30)
    # url = 'http://10.0.1.163:8080/jenkins/job/sprdroid4.4_sfphone_17f_rls1/lastBuild/artifact/Images/sp9820e_2h10_native-userdebug-native/sp9820e_2h10_native-userdebug-native_MOCER5_2H10_UNCACHE_SIGNE.pac.gz'
    # verifyid = '214'
    # download_pac(url, verifyid)


