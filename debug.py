import requests


# python submit_for_testing.py \
#       --device-type {LAVA_DEVICE_TYPE} \
#       --build-number  {build_number}\
#       --lava-server {LAVA_SERVER} \
#       --qa-server {QA_SERVER} \
#       --qa-server-team lkft \
#       --qa-server-project {QA_SERVER_PROJECT} \
#       --test-plan {LAVA_DEVICE_TYPE}/{yaml} \
#       --img-path {DOWNLOAD_URL} \
#       --change-id {changeid} \
#       --vts-url {VTS_URL} \
#       --submitter {SUBMIT_USER_NAME} \
#       --qa-token 13194653496cba5209fd1187e37adb5c0260f904
def request_squrd(download_path, daily_url, dailyid):
    dtl = requests.get('http://10.0.70.128:8000/submitinfos/infos/list_pac_urls_j/').json()
    device_type = dtl.get(daily_url)
    dp = 'http://worker05:8080/'+download_path
    url_s = daily_url.split('/')
    if 'view' in daily_url:
        branch = url_s[7]
    else:
        branch = url_s[5]

    project_i = url_s.index('Images') + 1
    project = url_s[project_i]

    b_num = branch+"_"+project+str(dailyid)
    y_template = os.join('template', device_type+'.yaml')
    cmd = """python submit_for_testing.py \
          --device-type {LAVA_DEVICE_TYPE} \
          --build-number  {build_number}\
          --lava-server {LAVA_SERVER} \
          --qa-server {QA_SERVER} \
          --qa-server-team lkft \
          --qa-server-project {QA_SERVER_PROJECT} \
          --test-plan {LAVA_DEVICE_TYPE}/{yaml} \
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
                changeid='',
                VTS_URL='',
                SUBMIT_USER_NAME='pac_dloader',
                )

    print cmd
    os.system(cmd)

if __name__ == '__main__':
    dtl = requests.get('http://10.0.70.128:8000/submitinfos/infos/list_pac_urls_j/').json()
    print type(dtl)
    print dtl