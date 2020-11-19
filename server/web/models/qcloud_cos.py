from utils import utils
from utils import cos_auth
from configs import config

_region = 'ap-guangzhou'


def _get_region_url(region='ap-guangzhou'):
    return f"http://{config.cos_bucket_name}-{config.cos_app_id}.cos.{region}.myqcloud.com"


def _get_upload_path(file_name):
    # print(config.cos_app_id, config.cos_bucket_name, file_name)
    return "/files/v2/{0}/{1}{2}".format(config.cos_app_id, config.cos_bucket_name, file_name)


def write(file_name, data):
    if file_name[0:1] != '/':
        file_name = '/' + file_name
    region_url = _get_region_url()
    url = region_url + _get_upload_path(file_name)
    params = {
        "op": "upload",
        "filecontent": data,
        "sha": utils.sha1(data),
        "biz_attr": "",
        "insertOnly": "0",
    }
    headers = {
        "Authorization": cos_auth.Auth.sign_more(config.cos_bucket_name, file_name, 0),
        "User-Agent": "jw-cos-python-sdk-v4",
    }
    return utils.cos_upload(url, headers, params)


def make_down_url(resource_path):
    l = resource_path.split("/")
    if len(l) != 5:
        return ''
    url = f"http://{config.cos_bucket_name}-{config.cos_app_id}.cos.{_region}.myqcloud.com/record/{l[4]}"
    return url
