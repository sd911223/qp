import oss2
from configs import config

endpoint = 'http://oss-cn-shenzhen-internal.aliyuncs.com'

auth = oss2.Auth(config.oss_secret_id, config.oss_secret_key)
bucket = oss2.Bucket(auth, endpoint, config.oss_bucket_name)


def write(file_name, data):
    return bucket.put_object(file_name, data)


def download(resource_path):
    l = resource_path.split("/")
    if len(l) != 4:
        return None
    key = '{0}/{1}'.format(l[2], l[3])
    return bucket.get_object(key).read()
