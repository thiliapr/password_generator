# thiliapr/password_generator
这是一个基于确定性算法的密码生成器，可以根据主密码和网站域名生成唯一且复杂的密码。

## 许可证
thiliapr/password_generator 是自由软件，遵循 [Affero GNU 通用公共许可证第 3 版或任何后续版本](https://www.gnu.org/licenses/agpl-3.0.html)。你可以自由地使用、修改和分发该软件，但不提供任何明示或暗示的担保。

## 设计理念
人们常说“不要在不同网站使用相同密码”，但又很难记住一大堆不同密码。  
本工具采用确定性算法，只需记住一个主密码，即可为不同网站生成不同的强密码，无需存储任何密码数据。  
换句话说，你就不用记那么多不同的密码了，只需要记住一个主密码就行了。

## 主要功能
- **确定性生成**: 相同输入永远产生相同输出
- **双重哈希引擎**:
  - 快速的 BKDR 哈希。向后兼容 [2023 年的黑历史的 C 版本](https://github.com/thiliapr/ThGenPwd)，主密码和服务名不能包含 Unicode 字符集，只能用标准 ASCII 字符集
  - 安全的 scrypt 哈希。默认，支持任意字符集甚至是字节串（自己找代码 API 调去吧）
- **可定制密码长度**: 支持无限位密码长度（但是注意，太长的密码可能产生循环）
- **跨平台**: 你可以在 Windows、Linux 甚至 Android 使用这个密码生成器。

## 快速开始
### 你需要什么
- Python 3.7 或更高版本
- 一个好记但强的主密码
- 你要生成密码的网站域名（如 `github.com`, `google.com`），我个人建议不要使用二级域名，而是使用一级域名，这样方便写（比如不用 `www.google.com`, 而是 `google.com`）

### 安装
```bash
# 克隆仓库
git clone https://github.com/thiliapr/password_generator.git
cd password_generator
```

### 基本使用
```bash
# 使用默认的 scrypt 引擎生成 16 位密码
python password_generator.py "私は夏色まつりが一番好きです！" "youtube.com"
# 指定密码长度
python password_generator.py "東方プロジェクトMusicIsTheBest" "touhou-project.news" -l 20
# 使用 BKDR 引擎（向后兼容，但不推荐用于新密码）
python password_generator.py "YouCannotUseUnicodeCharactersHere" "github.com" -e bkdr
# 静默模式（仅输出密码，不显示耗时信息）
python password_generator.py "AuthorIsLearningJapaneseInDuolingoToListenASMR..." "duolingo.com" -q
```

## 安全注意事项
### ⚠️ 警告
1. **主密码安全**: 主密码泄露意味着所有派生密码泄露
2. **无密码恢复**: 忘记主密码 = 丢失所有密码
3. **网站限制**: 某些网站可能有特殊字符限制，可能需要手动调整

### 🔐 最佳实践
1. **选择强主密码**: 允许 Unicode 字符集，你可以写中文、英语、日语、俄语、世界语、阿拉伯语、数学符号、Emoji，甚至混着写，只要你记得住。如果你这么做，攻击者想想计算量就开心了
2. **备份主密码**: 写在纸上，存放在安全的地方，比如你家保险柜
3. **不要使用可能泄露了的主密码**: 如果你用 BKDR 生成过密码，那就不要再在新版 scrypt 引擎使用这个主密码。为什么？因为虽然攻击者难以破解 scrypt 的密码参数，但是却很容易破解 BKDR 引擎生成的参数。攻击者可能通过以前网站泄露的密码找到你的主密码，所以它变得不安全了

## 迁移指南
### 从 BKDR 迁移到 scrypt
如果你之前使用 BKDR 引擎生成的密码:
1. 记录所有使用 BKDR 生成的网站密码
2. 为每个网站使用 scrypt 引擎生成新密码
3. 更新网站密码

## 常见问题
```plaintext
Q: scrypt 引擎为什么这么慢？
A: 慢 = 抗暴力破解。你能接受密码生成 1 秒的延迟，但攻击者不能。攻击者想要暴力尝试 1000 密码需要 16.7 分钟。
```
