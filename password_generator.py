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
from collections.abc import Callable
import hashlib
from typing import Iterator, Optional


# Hash 函数一览
HashFunction = Callable[[str], int]
HASH_FUNCTION: dict[str, HashFunction] = {}


def register_hash_function(name: str):
    def wrapper(func: HashFunction) -> HashFunction:
        HASH_FUNCTION[name] = func
        return func
    return wrapper


@register_hash_function("bkdr")
def bkdr_hash(input_str: str) -> int:
    """
    来源: https://byvoid.com/zhs/blog/string-hash-compare/
    我在 C 的实现中的 BKDR 哈希算法就是抄的这里，然后标上了来源
    这是 2008 年的文章，我在 2023 年写的时候随便搜索到的，然后就直接用了

    保留它是因为我的很多网站密码都是用它生成的，新的网站密码生成器用更安全的 scrypt 算法，旧的网站密码生成器继续用它
    """
    hash_value = 0
    for char in input_str:
        hash_value = hash_value * 131 + ord(char)
    # 确保哈希值是 32 位正整数（因为当时我还在用 32 位系统，在 C 的实现中没有 uint64_t）
    hash_value &= 0x7FFFFFFF
    return hash_value


@register_hash_function("scrypt")
def special_scrypt(input_str: str) -> int:
    return int.from_bytes(hashlib.scrypt(
        hashlib.sha3_512(input_str.encode("utf-8")).digest(),
        # 我应该用 4th 的，但木已成舟
        salt=b"June 4, 1989" + hashlib.sha3_256(input_str.encode()).digest(),
        # 这套参数在我的电脑跑 1 second per hash
        n=2 ** 16, r=8, p=2,
        # 防止报爆内存的异常
        maxmem=1024 ** 2 * 128,
        # 我才知道这玩意也是参数
        dklen=64
    ), byteorder="big")


# 密码生成函数
def generate_password(dividend: int, divisor: int) -> Iterator[str]:
    # 有个专业的名称是欧几里得除法，或者带余除法，不过我管他叫小学除法，因为小学学的就是这种
    # 127 进制除法
    BASE_NUMBER = 127
    # 当时瞎鸡巴乱想写出来的，不太靠谱，但事已至此，兼容已经生成了的密码
    PASSWORD_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ`_~@#$%^&*-=:;,.-"

    while True:
        # 朴实无华且枯燥的除法
        quotient, remainder = divmod(dividend, divisor)
        dividend = remainder * BASE_NUMBER
        # 在密码字符集里找商位置的字符，作为密码字符
        yield PASSWORD_CHARS[quotient % len(PASSWORD_CHARS)]


# 主函数
def parse_args(args: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="根据两个输入字符串生成确定性密码")
    parser.add_argument("seed_string", type=str, help="用于密码生成的主字符串，推荐使用你自己的私人密码，比如: 超絶かわいい夏色まつりちゃん")
    parser.add_argument("modifier_string", type=str, help="修改生成序列的次字符串，推荐使用网站域名或服务名称，比如: gfw.report")
    parser.add_argument("-l", "--length", type=int, default=16, help="生成密码的长度，默认为 %(default)s")
    parser.add_argument("-e", "--engine", type=str, choices=HASH_FUNCTION.keys(), default="scrypt", help="选择哈希引擎，默认为 %(default)s")
    return parser.parse_args(args)


def main(args: argparse.Namespace):
    # 根据选择的哈希引擎初始化密码生成器
    seed_hash, modifier_hash = [HASH_FUNCTION[args.engine](string) for string in [args.seed_string, args.modifier_string]]

    # 迭代生成密码字符
    password = []
    for char, _ in zip(generate_password(seed_hash, modifier_hash), range(args.length)):
        password.append(char)
    print("".join(password))


if __name__ == "__main__":
    main(parse_args())
