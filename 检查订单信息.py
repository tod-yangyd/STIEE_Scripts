

from msedge.selenium_tools import Edge, EdgeOptions
from time import sleep





login = 'https://pi.stiee.com/#/login'
orderlist_url = 'https://pi.stiee.com/#/order/orderList'
header = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.49'

options = EdgeOptions()
options.use_chromium = True
options.binary_location = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" # 浏览器的位置




def get_orderinfo(driver):
    row=driver.find_elements_by_tag_name('tr')
    list=[]
    for i in row:
        find_order = False
        j=i.find_elements_by_tag_name('td')
        for item in j:
            text=item.text
            if text == '22SAS01P16D32-00296':
                find_order = True
        if find_order == True:
            return item


 
if __name__ == "__main__":
    driver = Edge(options=options, executable_path=r"D:\YYD\WorkSpace\msedgedriver.exe") # 相应的浏览器的驱动位置
    driver.get(login)
    username = driver.find_element_by_name("userName") #输入账户
    username.send_keys('###')

    userpswd = driver.find_element_by_name("password") #输入密码
    userpswd.send_keys('###')
    driver.find_element_by_xpath('/html/body/div/div/div/div/form/div[3]/div/button').click() #登录
    sleep(2)


    driver.get(orderlist_url)
    sleep(5)
    driver.find_element_by_xpath('/html/body/div[1]/div/div/div/div[2]/div[1]').click() #打开搜索框
    sleep(5)
    order_input = driver.find_element_by_xpath('/html/body/div[1]/div/div/div/div[2]/div[1]/div/div[2]/div/form/div[2]/div/div/input')
    order_input.send_keys = ('22SAS01P16D32-00296')
    driver.find_element_by_xpath('/html/body/div[1]/div/div/div/div[2]/div[1]/div/div[2]/div/form/div[16]/div/button[1]').click() #查询数据


    sleep(2)


    target = get_orderinfo(driver) #获取gateway的健康实例数
    driver.quit
    print(target)   
