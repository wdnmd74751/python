import requests
import parsel
import csv
import time

cookies='your cookies'
cookies_jar = requests.cookies.RequestsCookieJar()
for cookie in cookies.split(";"):
    key, value = cookie.split('=', 1)
    cookies_jar.set(key, value)

headers = {
    'user-agent': 'your user-agent'
}

def write_to_csv(writer, data_dict, f):
    """
    安全地写入数据到CSV文件
    """
    try:
        writer.writerow(data_dict)
        f.flush()  # 立即将数据写入文件
        return True
    except Exception as e:
        print(f"写入CSV时发生错误: {str(e)}")
        return False

def main():
    with open('data_1.csv', mode='w', encoding='utf-8', newline='') as f:
        writer = None
        is_first = True

        for page in range(50,101):
            print(f'==========正在采集第{page}页的数据内容=========')
            url = f'https://nb.lianjia.com/ershoufang/pg{page}/'
            
            try:
                respond = requests.get(url=url, headers=headers, cookies=cookies_jar)
                respond.raise_for_status()  # 检查请求是否成功
                html = respond.text
                selector = parsel.Selector(html)
                lis = selector.css('.sellListContent li .info')
                
                for house_index, li in enumerate(lis, 1):
                    try:
                        district = li.css('.flood .positionInfo a::text').getall()
                        href = li.css('.info .title a::attr(href)').get()
                        totalPrice = li.css('.priceInfo .totalPrice span::text').get()
                        singalPrice = li.css('.priceInfo .unitPrice::attr(data-price)').get()

                        if not href:
                            print(f"第{page}页第{house_index}个房屋未获取到详情链接，跳过该房屋")
                            continue

                        # 获取详细信息
                        response = requests.get(url=href, headers=headers, cookies=cookies_jar)
                        response.raise_for_status()
                        html_1 = response.text
                        selector = parsel.Selector(html_1)

                        # 基本属性
                        lis_2 = selector.css('.baseinform .introContent .base')
                        base_labels = lis_2.css('.content ul li .label::text').getall()
                        base_values = lis_2.css('span.label').xpath('following-sibling::text()').getall()
                        base_values = [item.strip() for item in base_values if item.strip()]

                        # 交易属性
                        lis_1 = selector.css('.baseinform .introContent .transaction')
                        transaction_labels = lis_1.css('.content ul li .label::text').getall()
                        transaction_values = lis_1.css('.content ul li span:last-child::text').getall()
                        transaction_values = [item.strip() for item in transaction_values]

                        # 构建数据字典
                        data_dict = {
                            '总价（万）': totalPrice,
                            '单价（元/平）': singalPrice,
                            '小区名': district[0] if district else '',
                            '所在地区': district[1] if len(district) > 1 else ''
                        }

                        # 添加基本属性到字典
                        for label, value in zip(base_labels, base_values):
                            label = label.strip().rstrip('：')
                            data_dict[label] = value

                        # 添加交易属性到字典
                        for label, value in zip(transaction_labels, transaction_values):
                            label = label.strip().rstrip('：')
                            data_dict[label] = value

                        # 如果是第一次循环，创建writer和写入表头
                        if is_first:
                            fieldnames = ['总价（万）', '单价（元/平）', '小区名', '所在地区']
                            fieldnames.extend([label.strip().rstrip('：') for label in base_labels])
                            fieldnames.extend([label.strip().rstrip('：') for label in transaction_labels])
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            f.flush()
                            is_first = False
                            print("CSV表头写入成功")

                        # 写入数据并验证
                        success = write_to_csv(writer, data_dict, f)
                        if success:
                            print(f"第{page}页第{house_index}条数据写入成功")
                        else:
                            print(f"第{page}页第{house_index}条数据写入失败")

                        time.sleep(1)

                    except requests.RequestException as e:
                        print(f"第{page}页第{house_index}个房屋链接访问失败，原因: {e}")
                        continue
                    except Exception as e:
                        print(f"处理第{page}页第{house_index}个房屋数据时出错: {e}")
                        continue

            except requests.RequestException as e:
                print(f"访问第{page}页失败，原因: {e}")
                continue
            except Exception as e:
                print(f"处理第{page}页时出错: {e}")
                continue

            time.sleep(2)

        print("数据采集完成并保存到data_1.csv")

if __name__ == "__main__":
    main()