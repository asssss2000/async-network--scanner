import asyncio


target_network="192.168.1"
host_range=range(1,255)
ports_to_scan=[80,443,445,8000,8800]
timeout=1.0
max_concurrency=500
scan_interval=30
show_only_changes=False


print_lock=asyncio.Lock()


async def scan_port(ip:str,port:int,timeout:float=1.0) -> bool:
    try:
        conn = asyncio.open_connection(ip, port)

        reader,writer=await asyncio.wait_for(conn,timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except Exception:
        return False
    
async def bounded_scan(sem:asyncio.Semaphore,ip:str,port:int,timeout:float):
    async with sem:
        is_open= await scan_port(ip,port,timeout)
        return (ip,port,is_open)
async def run_scan(last_state:dict | None=None)-> dict:

    sem=asyncio.Semaphore(max_concurrency)
    task=[]
    for i in host_range:
        ip=f"{target_network}.{i}"
        for port in ports_to_scan:
            task.append(asyncio.create_task(bounded_scan(sem,ip,port,timeout)))

    current_state:dict[tuple[str,int],bool]={}


    for coro in asyncio.as_completed(task):
        ip, port, is_open = await coro
        current_state[(ip, port)] = is_open

        # چاپ خروجی
        if show_only_changes and last_state is not None:
            prev = last_state.get((ip, port))
            if prev != is_open:
                async with print_lock:
                    print(f"{ip}:{port} -> {'OPEN' if is_open else 'CLOSED'}")
        else:
            if is_open:
                async with print_lock:
                    print(f"[OPEN] {ip}:{port}")

    return current_state

async def main():
    """
    حلقه‌ی مانیتورینگ مداوم
    """
    last_state = None
    while True:
        async with print_lock:
            print("شروع اسکن جدید ...")
        last_state = await run_scan(last_state if show_only_changes else None)
        async with print_lock:
            print("----- پایان این دور اسکن -----\n")
        await asyncio.sleep(scan_interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("خروج با CTRL+C")

    
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time

# # راه‌اندازی خودکار Chrome Driver (بهترین روش)
# service = Service(ChromeDriverManager().install())
# driver = webdriver.Chrome(service=service)

# # یا راه‌اندازی دستی (اگر درایور را خودتان دانلود کردید)
# # driver = webdriver.Chrome(executable_path='مسیر/به/chromedriver')

# # باز کردن یک صفحه وب
# driver.get("https://www.google.com")

# # پیدا کردن یک element (مثلاً کادر جستجو) و تعامل با آن
# search_box = driver.find_element(By.NAME, "q")  # استفاده از By برای مشخص کردن نوع selector
# search_box.send_keys("Selenium Python tutorial")  # تایپ کردن در کادر
# search_box.send_keys(Keys.RETURN)  # فشردن دکمه Enter

# # منتظر ماندن برای بارگذاری نتایج
# wait = WebDriverWait(driver, 10)  # حداکثر 10 ثانیه منتظر بمان
# search_results = wait.until(EC.presence_of_element_located((By.ID, "search")))

# # گرفتن screenshot از صفحه
# driver.save_screenshot("search_results.png")

# # بستن مرورگر
# driver.quit()