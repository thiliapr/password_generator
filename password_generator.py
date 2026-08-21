# Copyright (C)  thiliapr 2025-2026
# Email: thiliapr@tutanota.com
# License: AGPLv3-or-later（不过真的会有人用这个代码吗？）

# 应用说明: 根据两个输入字符串生成确定性密码
# 人们常说“不要在不同网站使用相同密码”，但又很难记住一大堆不同密码
# 这个脚本可以根据你的单一私人密码和网站域名，生成每个网站都不同的密码
# 只要你记住你的私人密码和网站域名，就能随时生成
# 不过要谨防私人密码泄露，否则所有网站的密码都会被攻破（这点和传统密码管理器一样）

# 更新日志 
# 2023: 写了 C 版本的密码生成器，使用 BKDR 哈希算法（回过头看，真是黑历史）
# 2025: 因为换电脑了，没有预编译版本，下载个 gcc 或者 msvc 又很麻烦，刚刚好又经常写 Python 脚本，于是将 C 版改写为 Python 版，优化了变量名和注释，精简代码
# 2026: 最近一时兴起丢给 AI 评析，发现不够安全（AI 评价“糟糕透顶！难以置信！建议代码作者趁早转行”），引入更强的 scrypt 哈希算法（这也是 AI 推荐的），作为默认选项

import argparse
import hashlib
import time
from typing import Iterator, Optional

# BKDR 哈希计算
BKDR_HASH_SEED = 131  # BKDR 哈希算法的种子值，历史遗留数字，我找的文档说最好是质数

# 密码生成
PASSWORD_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`_~@#$%^&*-=:;,.-"  # 自己打的，然后删了一些网站禁止使用的字符
BASE_NUMBER = 127  # 密码生成的基数。我们都知道，任何分数都可以表示为无限循环小数，小数的循环节长度与分母和基数有关——当基数是质数时，循环节长度最长，而 127 是小于 128 的最大质数，所以就用它了
DEFAULT_LENGTH = 16  # 默认密码长度，历史遗留数字，网站密码一般限制在 8-16 字符之间

# Scrypt 哈希计算
SCRYPT_BYTEORDER = "big"  # 必须固定字节序，否则不同平台生成的密码会不一样。因为 Python 默认是大端序，所以就用大端序了
# 经过一系列测试，这组参数能在 1 秒左右生成 16 字符密码（足够快了），还比较安全，所以就用它了
SCRYPT_N = 2 ** 16
SCRYPT_R = 8
SCRYPT_P = 2
SCRYPT_DKLEN = 64
SCRYPT_MAXMEM = 1024 ** 2  * 128  # 防止报内存不足错误（ValueError: [digital envelope routines] memory limit exceeded）
# 某东方大国的一件重大历史事件，历史不应……算了，记不记随缘，毕竟没有人有义务记住历史
SCRYPT_SALT_PREFIX = b"June 4, 1989"


class Placeholder:
    def return_self(self, *args, **kwargs):
        return self

    __getattr__ = __call__ = return_self


class TimeRecoder:
    def __init__(self):
        self.start_time = time.perf_counter()
        self.last_time = self.start_time

    def record(self, label: str):
        current_time = time.perf_counter()
        print(f"{label}: {current_time - self.last_time:.3f} 秒")
        self.last_time = current_time

    def total(self, label: str):
        current_time = time.perf_counter()
        print(f"{label}: {current_time - self.start_time:.3f} 秒")
        self.last_time = current_time



def bkdr_hash(input_str: str) -> int:
    """
    来源: https://byvoid.com/zhs/blog/string-hash-compare/
    我在 C 的实现中的 BKDR 哈希算法就是抄的这里，然后标上了来源
    这是 2008 年的文章，我在 2023 年写的时候随便搜索到的，然后就直接用了
    """
    hash_value = 0
    for char in input_str:
        hash_value = hash_value * BKDR_HASH_SEED + ord(char)
    # 确保哈希值是32位正整数（因为当时我还在用 32 位系统，在 C 的实现中没有 uint64_t）
    hash_value &= 0x7FFFFFFF
    return hash_value


def generate_password(seed_hash: int, modifier_hash: int) -> Iterator[str]:
    # 小学除法立大功
    while True:
        # 整数除法获取商和余数
        quotient, remainder = divmod(seed_hash, modifier_hash)

        # 将商映射到密码字符集
        yield PASSWORD_CHARS[quotient % len(PASSWORD_CHARS)]

        # 更新种子值: 余数乘以基数，作为下一轮的被除数
        seed_hash = remainder * BASE_NUMBER


def generate_password_by_bkdr(seed_str: str, modifier_str: str) -> Iterator[str]:
    """
    为了兼容我在 2023 年用 C 写的同款密码生成器。那都是历史遗留问题了，黑历史啊[捂脸]
    测试效果: 0.001 秒生成 16 字符密码，太快了，容易被暴力破解
    保留它是因为我的很多网站密码都是用它生成的，新的网站密码生成器用更安全的 scrypt 算法，旧的网站密码生成器继续用它
    """
    seed_hash = bkdr_hash(seed_str)
    modifier_hash = bkdr_hash(modifier_str)
    return generate_password(seed_hash, modifier_hash)


def generate_password_by_scrypt(seed_str: str, modifier_str: str) -> Iterator[str]:
    """
    真正遥遥领先的哈希生成器
    测试效果: 0.998 秒生成 16 字符密码，安全性大幅提升
    """
    seed_hash, modifier_hash = [
        int.from_bytes(hashlib.scrypt(
            hashlib.sha3_512(x.encode("utf-8")).digest(),  # 保证输入长度足够
            salt=SCRYPT_SALT_PREFIX + hashlib.sha3_256(x.encode()).digest(),
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
            maxmem=SCRYPT_MAXMEM,
            dklen=SCRYPT_DKLEN
        ), byteorder=SCRYPT_BYTEORDER)
        for x in [seed_str, modifier_str]
    ]
    return generate_password(seed_hash, modifier_hash)


def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="根据两个输入字符串生成确定性密码")
    parser.add_argument("seed_string", type=str, help="用于密码生成的主字符串，推荐使用你自己的私人密码")
    parser.add_argument("modifier_string", type=str, help="修改生成序列的次字符串，推荐使用网站域名或服务名称")
    parser.add_argument("-l", "--length", type=int, default=DEFAULT_LENGTH, help=f"生成密码的长度(默认: {DEFAULT_LENGTH})")
    parser.add_argument("-e", "--engine", type=str, choices=["bkdr", "scrypt"], default="scrypt", help="选择哈希引擎(默认: %(default)s)")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式，不输出额外信息")
    return parser.parse_args(args)


def main(args: argparse.Namespace):
    # 记录耗费时间
    recoder = Placeholder() if args.quiet else TimeRecoder()

    # 根据选择的哈希引擎初始化密码生成器
    # 真正的耗时大头在这里，尤其是 scrypt 算法
    if args.engine == "bkdr":
        password_generator = generate_password_by_bkdr(args.seed_string, args.modifier_string)
    else:
        password_generator = generate_password_by_scrypt(args.seed_string, args.modifier_string)
    recoder.record("获取哈希")

    # 迭代生成密码字符
    # 不过实际上生成每个字符用时不超过 0.0001 秒，可以忽略不计
    for _ in range(args.length):
        print(next(password_generator), flush=True, end="")

    # 密码后添加换行符，并打印总耗时
    print()
    recoder.record("生成密码")
    recoder.total("总耗时")


if __name__ == "__main__":
    main(parse_args())
