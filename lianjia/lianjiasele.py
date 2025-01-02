from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.keys import Keys
import csv
import os
star_time = time.time()
def setup_driver():
    pass
    # Set up Edge options
    edge_options = Options()
    edge_options.add_argument('--start-maximized')
    edge_options.add_argument('your user-agent')
    
    # Initialize the Edge driver
    driver = webdriver.Edge(options=edge_options)
    
    # 首先访问链家网站的域名
    driver.get("https://nb.lianjia.com")
    time.sleep(1)
    # 在这里添加你的cookies
    #示例格式如下：
    cookies = 'your cookies'
    
    for cookie in cookies:
        driver.add_cookie(cookie)
    
    # 添加完cookie后刷新页面
    driver.refresh()
    
    return driver

def get_property_details(driver, href):
    pass
    try:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(href)
        
        # Wait for base information to load with timeout
        try:
            base_section = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.baseinform .introContent .base'))
            )
            
            # Get base attributes
            base_labels = [elem.text for elem in base_section.find_elements(By.CSS_SELECTOR, '.content ul li .label')]
            base_values = [elem.text.strip() for elem in base_section.find_elements(By.CSS_SELECTOR, '.content ul li')]
            base_values = [value.replace(label, '').strip() for label, value in zip(base_labels, base_values)]
            
            # Get transaction attributes
            transaction_section = driver.find_element(By.CSS_SELECTOR, '.baseinform .introContent .transaction')
            transaction_labels = [elem.text for elem in transaction_section.find_elements(By.CSS_SELECTOR, '.content ul li .label')]
            transaction_values = [elem.text.strip() for elem in transaction_section.find_elements(By.CSS_SELECTOR, '.content ul li span:last-child')]
            
            details = {
                'base_attributes': dict(zip(base_labels, base_values)),
                'transaction_attributes': dict(zip(transaction_labels, transaction_values))
            }
        except Exception as e:
            print(f"页面加载超时或元素未找到: {str(e)}")
            details = {'base_attributes': {}, 'transaction_attributes': {}}
    
    except Exception as e:
        print(f"访问链接失败: {str(e)}")
        details = {'base_attributes': {}, 'transaction_attributes': {}}
    
    finally:
        try:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
        except Exception as e:
            print(f"关闭标签页时出错: {str(e)}")
    
    return details
def write_to_csv(writer, data_dict, csv_file):
    """
    写入数据到CSV并确保写入成功
    """
    try:
        writer.writerow(data_dict)
        csv_file.flush()  # 立即将数据写入文件
        os.fsync(csv_file.fileno())  # 确保数据被写入磁盘
        return True
    except Exception as e:
        print(f"写入CSV时发生错误: {str(e)}")
        return False


def scrape_lianjia():
    driver = setup_driver()
    csv_file = open('lianjia_data.csv', 'w', newline='', encoding='utf-8')
    writer = None
    
    try:
        for page in range(1, 3):
            print(f'==========正在采集第{page}页的数据内容=========')
            url = f'https://nb.lianjia.com/ershoufang/pg{page}/'
            try:
                driver.get(url)
                time.sleep(5)
                for a in range(1, 8):
                    driver.execute_script("window.scrollBy(0, 500);")
                    driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(0.5)
                
                # Wait for property listings to load
                try:
                    listings = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.sellListContent li .info'))
                    )
                except Exception as e:
                    print(f"第{page}页加载失败，跳过该页: {str(e)}")
                    continue
                
                for listing_index, listing in enumerate(listings):
                    
                    try:
                        # Extract basic information
                        district_elements = listing.find_elements(By.CSS_SELECTOR, '.flood .positionInfo a')
                        district = [elem.text for elem in district_elements]
                        href = listing.find_element(By.CSS_SELECTOR, '.title a').get_attribute('href')
                        
                        if not href:
                            print(f"第{page}页第{listing_index + 1}条数据链接无效，跳过")
                            continue
                            
                        total_price = listing.find_element(By.CSS_SELECTOR, '.priceInfo .totalPrice span').text
                        single_price = listing.find_element(By.CSS_SELECTOR, '.priceInfo .unitPrice').get_attribute('data-price')
                        
                        # Get detailed property information
                        details = get_property_details(driver, href)
                        
                        # 如果详情页获取失败，跳过该条数据
                        if not details['base_attributes'] and not details['transaction_attributes']:
                            print(f"第{page}页第{listing_index + 1}条数据详情获取失败，跳过")
                            continue
                        
                        time.sleep(3)
                        
                        # 整理数据
                        base_dict = details['base_attributes']
                        transaction_dict = details['transaction_attributes']
                        
                        data_dict = {
                            '总价（万）': total_price,
                            '单价': single_price,
                            '小区名': district[0] if district else '',
                            '所在地区': district[1] if len(district) > 1 else '',
                            **base_dict,
                            **transaction_dict
                        }
                        
                        # 如果是第一条数据，创建CSV文件并写入表头
                        if writer is None:
                            fieldnames = ['总价（万）', '单价', '小区名', '所在地区'] + \
                                       list(base_dict.keys()) + \
                                       list(transaction_dict.keys())
                            
                            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                            writer.writeheader()
                            csv_file.flush()
                            print("CSV表头写入成功")
                        
                        # 写入数据并验证
                        print(f"正在写入数据：{data_dict}")
                        success = write_to_csv(writer, data_dict, csv_file)
                        if success:
                            print(f"第{page}页第{listing_index + 1}条数据写入成功")
                        else:
                            print(f"第{page}页第{listing_index + 1}条数据写入失败")
                        
                        time.sleep(1)
                    
                    except Exception as e:
                        print(f"处理第{page}页第{listing_index + 1}条数据时出错: {str(e)}")
                        continue
                
            except Exception as e:
                print(f"处理第{page}页时出错: {str(e)}")
                continue
            
            time.sleep(5)
    
    finally:
        if csv_file:
            csv_file.close()
        driver.quit()

if __name__ == "__main__":
    scrape_lianjia()
    end_time = time.time()
    print(f'运行时间：{end_time-star_time}')
