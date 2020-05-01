# 完成词语的网页排名和搜索功能

# 网页排名-使用TF/IDF；
# TF--词频，即词条t在文档d中的频率
# IDF--逆文本频率指数，如果包含词条t的文档越少，则词条t的IDF越大，说明词条t具有很好的类别区分能力
import math
import sqlite3
from urllib import response, request

import jieba
from bs4 import BeautifulSoup

conn = sqlite3.connect("viewsdu.db")
c = conn.cursor()
c.execute('select count(*) from doc')
N = 1 + c.fetchall()[0][0]   # 文档总数
#  print(N)
target = input('请输入搜索词：')
seggen = jieba.cut_for_search(target)  # 将目标搜索词进行分词操作
score = {}   # 用于存储“文档号：文档得分”
for word in seggen:
    print("得到查询词：", word)
    tf = {}  # 文档号：次数例如：{12:1}
    c.execute("select list from word where term=?", (word,))
    result = c.fetchall()
    # 查询词在word表中
    if len(result) > 0:
        doclist = result[0][0]  # 得到word所在文档ID组成的字符串,例如"12 56 13 65 98“
        doclist = doclist.split(' ')
        doclist = [int(x) for x in doclist]   # 字符串转为int类型的元组[12，56,13,65,98]

        # 计算IDF，即word出现的文档总数在总文档总数中占得比例
        df = len(set(doclist))  # 当前word对应的df，即word所在的文档总数，注意set集合进行去重
        idf = math.log(N/df)
        print('idf:', idf)

        # 计算TF,即word在文档出现频率
        # 统计word在出现的文档中出现的次数，使用tf字典记性记录,{num:count}
        for num in doclist:
            if num in tf:
                tf[num] += 1
            else:
                tf[num] = 1

        # 统计每篇文档在word中的得分情况
        # 使用score记录word在出现过的文档中的得分，{num:score}
        for num in tf:
            if num in score:
                # 如果该num文档已经有分数了，则累加
                score[num] += tf[num] * idf
            else:
                score[num] = tf[num] * idf
#  对score字典进行字典d的值排序
sortedlist = sorted(score.items(), key=lambda d:d[1], reverse=True)
# print('得分列表：', sortedlist)
cnt = 0
for num, docscore in sortedlist:
    cnt += 1
    c.execute('select link from doc where id=?', (num,))
    url = c.fetchall()[0][0]
    print(url, '得分：', docscore)
    try:
        response = request.urlopen(url)
        content = response.read().decode('utf-8')
    except:
        print('...读取网页出错')
        continue
    #  解析网页输出标题
    soup = BeautifulSoup(content, 'lxml')
    title = soup.title
    if title == None:
        print('no title')
    else:
        title = title.text
        print(title)
    if cnt > 20:
        break
if cnt == 0:
    print('搜索无效')