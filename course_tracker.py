from selenium import webdriver
from selenium.webdriver.support.ui import Select
import re, os, sys, time, json, requests
from getch import pause
from os import listdir
from os.path import isfile, join

# Open the browser with headless mode
url = "https://course.ncku.edu.tw/index.php?c=qry_all"
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--window-size=1920,1080") 
chrome_options.add_argument("--disable-extensions") 
chrome_options.add_argument("--proxy-server='direct://'") 
chrome_options.add_argument("--proxy-bypass-list=*") 
chrome_options.add_argument("--start-maximized") 
chrome_options.add_argument('--headless') 
chrome_options.add_argument('--disable-gpu') 
chrome_options.add_argument('--disable-dev-shm-usage') 
chrome_options.add_argument('--no-sandbox') 
chrome_options.add_argument('--ignore-certificate-errors') 

# Check which version of chromedriver can be used
versions = [f for f in listdir("./chromedriver") if isfile(join("./chromedriver", f))]
for version in versions:
    try:
        chromedriver_path = "./chromedriver/"+version
        browser = webdriver.Chrome(executable_path=chromedriver_path, chrome_options=chrome_options)
        break
    except:
        continue
browser.get(url)

def lineNotifyMessage(token, msg):
    headers = {
        "Authorization": "Bearer " + token, 
        "Content-Type" : "application/x-www-form-urlencoded"
    }

    payload = {'message': msg}
    r = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)
    return r.status_code

def crawl_course(department_name, search_class):
    search_result = []
    try:
        browser.find_element_by_xpath("//*[contains(text(), '" + department_name + "') and @class='btn_dept']").click()
        time.sleep(.5)
        table_field = browser.find_element_by_xpath("//table[contains(@class, 'table table-bordered')]")
        tr_field = table_field.find_elements_by_tag_name('tr')
        for element in browser.find_element_by_id('A9-table').find_elements_by_xpath(".//td//div[@class='dept_seq']"):  
            # Filter the course with no Course Number
            if element.text:
                # Get the Course Number
                course_no = element.text
                # Check the Course Number is matching with the Search Number
                if course_no != search_class:
                    continue
                else:
                    # Find the parent tag <tr> of Course Number
                    tr = element.find_element_by_xpath("..//..")
                    # Get the Course Name
                    course_name = tr.find_element_by_xpath(".//td//span[@class='course_name']").text
                    # Get the Teacher
                    teacher = tr.find_elements_by_xpath(".//td[@class='sm']")[0].text
                    #  Get the Introduction of course
                    introduction = tr.find_elements_by_xpath(".//td[@class='sm']")[1].find_element_by_tag_name('a').get_attribute('href')
                    # Get the Credit
                    credit = tr.find_elements_by_xpath(".//td[@align='center']")[0].text
                    total_left = tr.find_elements_by_xpath(".//td[@align='center']")[1].text
                    # Get the total select number
                    total_select = total_left.split('/')[0]
                    # Get the left number
                    left_select = total_left.split('/')[1]
                    # Get the time and location of course
                    time_location = [td.text for td in tr.find_elements_by_tag_name('td') \
                                    if re.match(r"\[(\d)\][A-Za-z0-9][~(\d)]*", td.text) or re.match(r"未定", td.text)][0]
                    search_result = [course_name, teacher, total_select, left_select]
                    # print("搜尋結果:\n課程代碼: {}\n課程名稱: {}\n授課老師: {}\n選課人數: {}\n餘額: {}\n上課時間/地點: \n{}"\
                    #     .format(course_no, course_name, teacher, total_select, left_select, time_location))
        time.sleep(.5)
        browser.back()
        if search_result:
            return "課程名稱: {}\n授課老師: {}\n選課人數: {}\n餘額: {}".format(search_result[0], search_result[1], search_result[2], search_result[3]), search_result[3]
        else:
            return 'Can not match course!!', None
    except KeyboardInterrupt:
        return 'KeyboardInterrupt', None
    except:
        return 'There are some error when crawling the website', None

def main():
    # Dictionary for { 'department number' : 'department code' }(e.g. {'F7' : '(F7)資訊系 CSIE'})
    department_no = {}
    # Store the searching courses(e.g. A9-220)
    search_list = []
    # Store the department name(e.g. (F7)資訊系 CSIE)
    search_dept_name_list = []
    # Read the lookup table and store into dictionary 
    print("Loading lookup table...")
    with open("dept_lookup.txt") as f:
        department_no = json.loads(f.read())
    os.system('cls')
    try:
        count = input('欲追蹤的數目: ')
    except KeyboardInterrupt:
        pause('按任意一鍵離開程式......')
        return
    # Enter the courses code that user want to track with
    for index in range(int(count)):
        try:
            search = input("{}.輸入課程代碼(e.g. A9-220): ".format(index+1))
            search_dept_no = search.split('-')[0]
            search_dept_name = department_no[search_dept_no]
            search_list.append(search)
            search_dept_name_list.append(search_dept_name)
        except KeyboardInterrupt:
            pause('按任意一鍵離開程式......')
            return
        except:
            os.system('cls')
            print("\r{0}\n".format('找不到對應系所資料...'), end="")
            pause('按任意一鍵離開程式......')
            return
    # Enter the LINE token for LINE Notify
    try:
        token = input('LINE權杖: ')
    except KeyboardInterrupt:
        pause('按任意一鍵離開程式......')
        return
    # Loop forever except the keyboard interruption or there has left for searching courses
    while True:
        try:
            output = ''
            result_list = []
            left_list = []
            for index in range(int(count)):
                search_result, left = crawl_course(search_dept_name_list[index], search_list[index]) 
                result_list.append(search_result)
                left_list.append(left)
                if left == None:
                    os.system('cls')
                    if search_result == 'Can not match course!!':
                        print ("\r{0}{1}{2}\n".format('找不到課程代碼 ', search_list[index], '的資訊...'), end="")
                        browser.close()
                    elif search_result == 'KeyboardInterrupt':
                        print ("\r{0}\n".format('Ctrl-C終止追蹤'), end="")
                    else:
                        print ("\r{0}\n".format('追蹤過程出現錯誤'), end="")
                    pause('按任意一鍵離開程式......')
                    return
                else:
                    output += str(search_result) + '\n' + str(time.ctime()) + '\n'
            os.system('cls')
            print ("\r{0}\n".format(output), end="")
            for index, element in enumerate(left_list):
                if element != '額滿':
                    os.system('cls')
                    message = '\nNO.'+str(index+1)+'\n'+str(result_list[index])+'\n系所編號: '+search_list[index].split('-')[0]+ \
                            '\n課程代號: '+search_list[index].split('-')[1]+'\n選課連結: https://course.ncku.edu.tw/index.php?c=auth'
                    if lineNotifyMessage(token, message) != 200:
                        print ("{0}\n".format('LINE token有誤'), end="")
                    else:
                        print("{0}\n".format('有餘額囉 : )'), end="")
                    browser.close()
                    pause('按任意一鍵離開程式......')
                    return
            time.sleep(.5)
        except KeyboardInterrupt:
            print ("\r{0}\n".format('終止追蹤'), end="")
            pause('按任意一鍵離開程式......')
            return            
    # Close the browser
    browser.close()

if __name__ == "__main__":
    main()