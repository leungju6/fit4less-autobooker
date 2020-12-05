from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

load_dotenv()
# set permissions for local chromedriver to test locally
start_url = "https://myfit4less.gymmanager.com/portal/login.asp"
chrome_options = Options()

# first condition just for debugging locally
if os.getenv("ENVIRONMENT") == "dev":
    chrome_options.add_argument("--kiosk") # use this for debugging on Linux/Mac
    # chrome_options.add_argument("--window-size=1920,1080") # use this for debugging on Windows
else:
    chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--kiosk") # use this for debugging on Linux/Mac
    chrome_options.add_argument("--window-size=3072,1920") # use this for debugging on Windows 3072 x 1920

driver = webdriver.Chrome(os.getenv("WEBDRIVER_PATH"), options=chrome_options)
driver.get(start_url)

try:
    # Login
    email_input = driver.find_element_by_id("emailaddress")
    password_input = driver.find_element_by_id("password")
    driver.implicitly_wait(1)
    email_input.send_keys(os.getenv("F4L_LOGIN"))
    password_input.send_keys(os.getenv("F4L_PASSWORD"))
    driver.implicitly_wait(5)
    password_input.send_keys(Keys.ENTER)
    driver.implicitly_wait(20)
    print("Logged In!")

    # Find your club
    if "F4L_CLUB" in os.environ:
        driver.find_element_by_id("btn_club_select").click()
        driver.implicitly_wait(5)
        all_clubs = driver.find_element_by_id("modal_clubs").find_element_by_class_name("dialog-content").find_elements_by_class_name("button")
        for club in all_clubs:
            if os.getenv("F4L_CLUB") == club.text:
                print("Club found: ", club.text)
                club.click()
                break
    
    driver.implicitly_wait(5)

    # Booking process for T+0, T+1, or T+2 days
    for i in range(3):
        if "TIME_SLOT" + str(i) not in os.environ:
            continue
        
        booking_date = str(datetime.now().date() + timedelta(days=i))
        driver.find_element_by_id("btn_date_select").click()  # day selector
        driver.implicitly_wait(20)
        driver.find_element_by_id("date_" + booking_date).click()
        driver.implicitly_wait(20)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.implicitly_wait(5)
    
        # check available_slots class 2nd index -> see if child elements exist
        available_slots = driver.find_elements_by_class_name("available-slots")[1].find_elements_by_class_name("time-slot-box")
        if len(available_slots) == 0:
            print("No available time slots for " + booking_date)
            continue
            
        d_slot = datetime.strptime(str(os.getenv("TIME_SLOT"+str(i))), '%I:%M%p')
            
        for slot in available_slots:
            a_slot = datetime.strptime(str(slot.text).split()[5] + str(slot.text).split()[6], '%I:%M%p')
            if d_slot <= a_slot:
                slot.find_element_by_xpath('..').click()
                driver.implicitly_wait(10)
                driver.find_element_by_id("dialog_book_yes").click()
                driver.implicitly_wait(10)
                print("Booked {} on {}".format(a_slot.strftime("%I:%M %p"),booking_date))
                break
            else:
                print("Skipping slot: {}".format(a_slot.strftime("%I:%M %p")))

except Exception as err:
    print(str(err))
finally:
    driver.quit()
