import requests
import re
import base64
import csv
from io import BytesIO
from lxml import etree
from fontTools.ttLib import TTFont


def creat_csv():
    '''
    创建 csv
    :return:
    '''
    with open('../data/data.csv','w',encoding='utf8',newline='') as f:
        head = ['标题','价格','户型','面积','朝向','楼层','装修','种类','位置','标签','设施','概况','链接']
        writer = csv.writer(f)
        writer.writerow(head)


def get_html(url):
    '''
    请求获取网页
    :param url:
    :return:
    '''
    headers = {
        'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    }
    response = requests.get(url,headers=headers)

    for i in range(3):
        if response.status_code == 200:
            response.status_code = 'utf8'
            return response.text
        else:
            continue


def get_links(html):
    '''
    提取此页中所有房源链接
    :param html:
    :return:
    '''
    html = etree.HTML(html)
    links = html.xpath('//div[@class="zu-itemmod"]/a[@class="img"]/@href')
    return links


def get_infos(html):
    '''
    提取房源中的详细信息
    :param html:
    :return:
    '''
    # 处理验证码
    if '访问过于频繁' in html:
        print('\n出现验证码，请手动刷新网页，按回车继续爬取。')
        tem = input()
        return
    else:
        try:
            parse_html = etree.HTML(html)
            # 标题
            title = parse_html.xpath('//div[@class="strongbox"]/text()')[0]
            # 价格
            price = parse_html.xpath('//span[@class="price"]/em/b/text()')[0]
            price = font_decode(price,html)
            price = str(price) + '元/月'

            house_info = parse_html.xpath('//li[@class="house-info-item"]')
            # 户型
            house_kind = house_info[0]
            house_kind = house_kind.xpath('./span[@class="info"]')[0]
            house_kind = house_kind.xpath('string(.)')
            num = re.findall('(.*?)室(.*?)厅(.*?)卫',house_kind)
            num = num[0][0] + num[0][1] + num[0][2]
            num = font_decode(num,html)
            house_kind = '{}室{}厅{}卫'.format(num[0],num[1],num[2])
            # 面积
            area = house_info[1]
            area = area.xpath('./span[@class="info"]/b/text()')[0]
            num = re.findall('(.*?)平方米',area)[0]
            num = font_decode(num,html)
            area = str(num) + '平方米'
            # 朝向
            dirs = house_info[2]
            dirs = dirs.xpath('./span[@class="info"]/text()')[0]
            # 楼层
            floor = house_info[3]
            floor = floor.xpath('./span[@class="info"]/text()')[0]
            # 装修
            decoration = house_info[4]
            decoration = decoration.xpath('./span[@class="info"]/text()')[0]
            # 类型
            kind = house_info[5]
            kind = kind.xpath('./span[@class="info"]/text()')[0]
            # 位置
            loc = house_info[6]
            loc = loc.xpath('string(.)')
            loc = loc.replace('\n','').replace(' ','')
            loc = loc.split('：')[1]

            # 标签
            label = parse_html.xpath('//ul[@class="title-label cf"]')[0]
            label = label.xpath('string(.)')
            label = label.replace('\n','').replace(' ','')

            # 设施
            facility = parse_html.xpath('//li[@class="peitao-item has"]')
            fs = ''
            for f in facility:
                f = f.xpath('./div[@class="peitao-info"]/text()')[0]
                fs += f + ','

            # 概况
            situation = parse_html.xpath('//div[@class="auto-general"]/b/text()')[0]

            return [title,price,house_kind,area,dirs,floor,decoration,kind,loc,label,situation,fs]
        except:
            return


def font_decode(num,html):
    '''
    破解字体反爬
    :param num:
    :return:
    '''
    # 保存字体映射文件
    font_url = re.findall("charset=utf-8;base64,(.*?)'\) format",html,re.S)[0]
    font_data = base64.b64decode(font_url)
    file = open('../output/font.woff','wb')
    file.write(font_data)
    file.close()

    # 保存为 xml
    fonts = TTFont('../output/font.woff')
    fonts.saveXML('../output/font.xml')

    font = TTFont(BytesIO(base64.decodebytes(font_url.encode())))
    c = font['cmap'].tables[0].ttFont.tables['cmap'].tables[0].cmap
    ret_list = []
    for char in num:
        decode_num = ord(char)
        if decode_num in c:
            num = c[decode_num]
            num = int(num[-2:]) - 1
            ret_list.append(num)
        else:
            ret_list.append(char)
    ret_str_show = ''
    for num in ret_list:
        ret_str_show += str(num)
    return ret_str_show


def write_to_csv(infos):
    '''
    写入每一条房源的数据
    :param infos:
    :return:
    '''
    with open('../data/data.csv','a+',encoding='utf8',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(infos)


if __name__ == '__main__':
    urls = 'https://sz.zu.anjuke.com/fangyuan/p{}/?from_price=0&to_price=2500'
    creat_csv()
    for p in range(1,51):
        url = urls.format(str(p))
        html = get_html(url)
        links = get_links(html)
        count = 1
        for link in links:
            html = get_html(link)
            if html == None:
                continue
            infos = get_infos(html)
            if infos == None:
                continue
            infos.append(link)
            write_to_csv(infos)
            print('已爬取第 %s 页，第 %s 条房源' % (str(p),str(count)))
            count += 1


