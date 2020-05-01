# 完成新闻内容的爬取和词语倒排表的建立

import re
import sqlite3
from collections import deque
from urllib import request
import jieba
from bs4 import BeautifulSoup

url = 'https://www.zut.edu.cn/index/xwdt.htm'  # URL入口

# 待爬取链接集合，使用广度遍历搜索
unvisited = deque()
# 已访问的链接集合
visited = set()
# 开始查找带爬取链接集合
unvisited.append(url)

# # 使用sqlite数据库，存储爬取到的链接
# conn = sqlite3.connect('viewsdu.db')
# c = conn.cursor()
# # 创建doc表，用于存储每个网页ID和URL链接
# c.execute('drop table doc')
# c.execute('create table doc(id int primary key, link text)')
# # 创建word表，即倒排表，用于存储词语和对应的网页ID的list
# c.execute('drop table word')
# c.execute('create table word(term varchar(25) primary key , list text)')
# conn.commit()
# conn.close()

print('****开始爬取****')
cnt = 0  # 记录爬取url的个数
print('开始.....')
while unvisited:
    url = unvisited.popleft()
    visited.add(url)
    cnt += 1
    print('开始爬取第',cnt , '个链接' ,url)

    # 爬取url的网页内容
    try:
        response = request.urlopen(url)
        content = response.read().decode('utf-8')
    except:
        continue
    # 解析网页内容，寻找下一个待爬取url
    soup = BeautifulSoup(content, 'lxml')
    all_a = soup.find_all('a', {'class':"c67214"})  # 本页面中所有的新闻链接<a>
    for a in all_a:
        # print(a.get('href'))
        x = a.get('href')  # 每条新闻的网址
        if re.match(r'http.+', x):
            if not re.match(r'http\:\/\/www\.zut\.edu\.cn\/.+', x):
                continue
        if re.match(r'\/info\/.+', x):
            x ='http://www.zut.edu.cn' + x
        elif re.match(r'info/.+', x):
            x ='http://www.zut.edu.cn/' + x
        elif re.match(r'\.\.\/info/.+', x):
            x ='http://www.zut.edu.cn' + x[2:]
        elif re.match(r'\.\.\/\.\.\/info/.+', x):
            x ='http://www.zut.edu.cn' + x[5:]
        # print(x)
        if (x not in visited) and (x not in unvisited):
            unvisited.append(x)
    # 下一页新闻的网址和尾页网址
    a = soup.find('a', {'class':"Next"})
    if a != None:
        x = a.get('href')
        if re.match(r'xwdt\/.+', x):
            x = 'http://www.zut.edu.cn/index/' + x
        else:
            x = 'http://www.zut.edu.cn/index/xwdt/' + x
        if (x not in visited) and (x not in unvisited):
            unvisited.append(x)

    # 网页链接爬取完毕，即所有的新闻链接都放在了网址队列unvisitied
    # 将爬取到的信息存放在数据库中，建立倒排词表word
    # 解析每个网页内容
    title = soup.title
    article = soup.find('div', class_='c67215_content', id='vsb_newscontent')
    author = soup.find('span', class_='authorstyle67215')
    time = soup.find('sapn', class_='timstyle67215')
    if title == None and article == None and author == None:
        print("无内容的页面")
        continue
    elif article == None and author == None:
        print('只有标题')
        title = title.text
        title = ''.join(title.split())
        article = ''
        author = ''
    elif article == None:
        print('有标题由作者，缺少内容')
        title = title.text
        title = ''.join(title.split())
        article = ''
        author = author.get_text("", strip=True)  # get_text()从大段html中提取文本，清空文本中间的html元素
        author = ''.join(author.split())
    elif author == None:
        print('有标题有内容，缺少作者')
        title = title.text
        title = ''.join(title.split())
        article = article.get_text("", strip=True)  # strip=True 去除前后空白
        article = ''.join(article.split())
        author = ''
    else:
        title = title.text
        title = ''.join(title.split())
        article = article.get_text("", strip=True)
        article = ''.join(article.split())
        author = author.get_text("", strip=True)
        author = ''.join(author.split())
    print('网页标题', title)

    # 提取出每个网页的title article author,对它们分别进行jieba分词，搜索引擎模式#下的分词
    seggen = jieba.cut_for_search(title)  # 搜索引擎模式下的jieba分词
    seglist = list(seggen)
    seggen = jieba.cut_for_search(article)
    seglist += list(seggen)
    seggen = jieba.cut_for_search(author)
    seglist += list(seggen)

    # 为每个词语建立倒排词表，存储在数据库viewsdu
    conn = sqlite3.connect("viewsdu.db")
    c = conn.cursor()
    # doc表中存入网页ID和网页链接
    c.execute('insert into doc values(?,?)', (cnt, url))
    # 为每个分出来的词建立倒排词表，即在word表中存入词语和其对应的网页ID
    for word in seglist:
        # 检查该词语是否已经在表中
        c.execute('select list from word where term = ?', (word,))
        result = c.fetchall()  # 即返回多个元组
        # 如果不存在
        if len(result) == 0:
            docliststr = str(cnt)
            c.execute('insert into word values(?,?)', (word, docliststr))
        # 如果已经存在
        else:
            docliststr = result[0][0]  # 得到词语对应元组的list属性
            docliststr += ' '+ str(cnt)
            c.execute('update word set list=? where term =?', (docliststr, word))
    conn.commit()
    conn.close()
print('词表建立完毕！')