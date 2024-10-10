import os
import time


def write_log(string, filename='', mode='a'):
    """
    将字符串写入文件

    Args:
      string: 要写入的字符串
      filename: 文件名
      mode: 写入模式，'a'为追加，'w'为覆盖，默认为追加

    Returns:
      None
    """
    if filename == '':
        now = time.localtime()
        filename = '/tmp/' + time.strftime("%Y-%m-%d_%H-%M-%S.log", now)

    # 创建目录（如果不存在）
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # 打开文件
    with open(filename, mode) as f:
        f.write(string + '\n')
