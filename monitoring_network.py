import asyncio

# Configuration
target_network = "192.168.1"
host_range = range(1, 255)
ports_to_scan = [80, 443, 445, 8000, 8800]
timeout = 1.0
max_concurrency = 500
scan_interval = 30
show_only_changes = False

# Lock for safe printing
print_lock = asyncio.Lock()

async def scan_port(ip: str, port: int, timeout: float = 1.0) -> bool:
    """
    Try to connect to a specific IP/port and check if it's open.
    """
    try:
        conn = asyncio.open_connection(ip, port)
        reader, writer = await asyncio.wait_for(conn, timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except Exception:
        return False
    
async def bounded_scan(sem: asyncio.Semaphore, ip: str, port: int, timeout: float):
    """
    Scan with semaphore to limit concurrency.
    """
    async with sem:
        is_open = await scan_port(ip, port, timeout)
        return (ip, port, is_open)

async def run_scan(last_state: dict | None = None) -> dict:
    """
    Run one full scan cycle.
    """
    sem = asyncio.Semaphore(max_concurrency)
    tasks = []
    for i in host_range:
        ip = f"{target_network}.{i}"
        for port in ports_to_scan:
            tasks.append(asyncio.create_task(bounded_scan(sem, ip, port, timeout)))

    current_state: dict[tuple[str, int], bool] = {}

    for coro in asyncio.as_completed(tasks):
        ip, port, is_open = await coro
        current_state[(ip, port)] = is_open

        # Output
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
    Continuous monitoring loop
    """
    last_state = None
    while True:
        async with print_lock:
            print("Starting new scan...")
        last_state = await run_scan(last_state if show_only_changes else None)
        async with print_lock:
            print("----- Scan cycle completed -----\n")
        await asyncio.sleep(scan_interval)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exiting with CTRL+C")


# Selenium example (commented out)
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time
#
# # Automatic Chrome Driver setup
# service = Service(ChromeDriverManager().install())
# driver = webdriver.Chrome(service=service)
#
# # Or manual setup if you downloaded the driver
# # driver = webdriver.Chrome(executable_path='path/to/chromedriver')
#
# # Open a web page
# driver.get("https://www.google.com")
#
# # Find an element (search box) and interact with it
# search_box = driver.find_element(By.NAME, "q")
# search_box.send_keys("Selenium Python tutorial")
# search_box.send_keys(Keys.RETURN)
#
# # Wait for results to load
# wait = WebDriverWait(driver, 10)
# search_results = wait.until(EC.presence_of_element_located((By.ID, "search")))
#
# # Take a screenshot
# driver.save_screenshot("search_results.png")
#
# # Close the browser
# driver.quit()
