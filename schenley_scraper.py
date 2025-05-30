from DrissionPage import ChromiumPage, ChromiumOptions
import csv
import time
import random

# --- Configuration ---
URL = "https://www.fastmoss.com/zh/e-commerce/detail/1729403466481308478"
CSV_FILE = 'schenley_reviews.csv'  # Output CSV file name
TOTAL_PAGES_TO_SCRAPE = 898  # Number of pages to scrape

# XPaths
COMMENT_SECTION_ROOT_XPATH = 'xpath:/html/body/div[1]/div/div[2]/div[2]/main/div[2]/div[7]/div[2]/div[4]'
# XPath for the container of all comment items on a page
COMMENT_ITEMS_LIST_XPATH = "xpath://*[@id='ai_comments']/div[2]/div[4]/div[2]"
STAR_XPATH = "xpath://ul[contains(@class, 'ant-rate')]/following-sibling::div[contains(@class, 'items-baseline')]/span[1]"
ITEM_XPATH = "xpath://div[contains(@class, 'relative max-w-fit')]/span[1]"
DATE_XPATH = "xpath://span[contains(@class, 'text-fmgray text-sm whitespace-nowrap')]"
REVIEW_XPATH = "xpath://span[contains(@class, 'text-sm text-fmblack')]"
# NEXT_BUTTON_XPATH will be dynamically generated

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"

def main():
    co = ChromiumOptions()
    co.set_user_agent(USER_AGENT)
    # co.set_argument('--headless') # For headless browsing
    page = ChromiumPage(co)
    
    initial_load_success = False
    try:
        print("Attempting to load URL...")
        page.get(URL)
        time.sleep(2) # Wait 2 seconds for initial load

        # print("Attempting to find comment items list container...")
        # # Scroll to the comment section before trying to find the element
        # comment_list_container_for_scroll = page.ele(COMMENT_ITEMS_LIST_XPATH)
        # if comment_list_container_for_scroll:
        #     comment_list_container_for_scroll.scroll(COMMENT_ITEMS_LIST_XPATH)
        #     print("Scrolled to comment items list container.")
        #     initial_load_success = True
        # else:
        #     print("comment_items_list_container NOT found for initial scroll. This may lead to scraping failure.")
        #     print(f"Scraping page 1 fail")
        #     page.quit()
        #     return

    except Exception as e:
        print(f"An exception occurred during initial page load and setup: {e}")
        print(f"Scraping page 1 fail")
        if page:
            page.quit()
        return
    
    # if not initial_load_success:
    #     print("Exiting main due to initial_load_success being false.")
    #     if page:
    #         page.quit()
    #     return

    # print("Initial page load and setup successful. Proceeding to scrape...")

    with open(CSV_FILE, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['Star', 'Item', 'Date', 'Review'])

        for page_num in range(1, TOTAL_PAGES_TO_SCRAPE + 1):
            page_scrape_successful_this_iteration = False
            print(f"Attempting to scrape page {page_num}...")
            try:
                # The page should already be scrolled to the correct section.
                # We find the container again, or assume it's still valid.
                # For robustness, it's often good to re-locate, but per instruction, no scroll after click.
                comment_items_list_container = page.ele(COMMENT_ITEMS_LIST_XPATH, timeout=10)

                if not comment_items_list_container:
                    print(f"Page {page_num}: Comment items list container NOT found. Cannot scrape this page.")
                    # This implies data scraping for this page failed.
                    # We might try to go to the next page or break.
                    # For now, we'll mark as fail and try to click next if not the last page.
                    page_scrape_successful_this_iteration = False
                else:
                    print(f"Page {page_num}: Comment items list container found.")
                    # Fetch all elements of each type. These should return lists of elements.
                    star_elements = comment_items_list_container.eles(STAR_XPATH)
                    item_elements = comment_items_list_container.eles(ITEM_XPATH)
                    date_elements = comment_items_list_container.eles(DATE_XPATH)
                    review_elements = comment_items_list_container.eles(REVIEW_XPATH)

                    # Determine the number of comments to process (should be 5, but take the minimum found)
                    num_comments = min(len(star_elements), len(item_elements), len(date_elements), len(review_elements))
                    
                    if num_comments == 0 and page_num == 1:
                        print(f"Page {page_num}: No comment data found on the first page. This might be an issue or an empty page.")
                    elif num_comments == 0:
                         print(f"Page {page_num}: No comment data found on this page.")


                    print(f"Page {page_num}: Found {len(star_elements)} stars, {len(item_elements)} items, {len(date_elements)} dates, {len(review_elements)} reviews. Processing {num_comments} comments.")

                    for i in range(num_comments):
                        star, item_text, date_text, review_text = "N/A", "N/A", "N/A", "N/A"
                        
                        if i < len(star_elements) and star_elements[i]:
                            star = star_elements[i].text.strip()

                        if i < len(item_elements) and item_elements[i] and item_elements[i].text.strip():
                            item_text = item_elements[i].text.strip()
                        else:
                            item_text = "Item: Default" 
                        
                        if i < len(date_elements) and date_elements[i]:
                            date_text = date_elements[i].text.replace('评论时间：', '').strip()
                        
                        if i < len(review_elements) and review_elements[i]:
                            review_text = review_elements[i].text.strip()
                        
                        writer.writerow([star, item_text, date_text, review_text])
                    
                    if num_comments > 0: # If we actually processed any comment data
                        page_scrape_successful_this_iteration = True
                    elif num_comments == 0 and comment_items_list_container: # Container found but no items
                        page_scrape_successful_this_iteration = True # Still count as "success" for page structure
                    else: # Neither container nor items found
                        page_scrape_successful_this_iteration = False


                if page_num < TOTAL_PAGES_TO_SCRAPE:
                    current_next_button_xpath = ""
                    if page_num < 4:
                        current_next_button_xpath = "xpath://*[@id='ai_comments']/div[2]/div[4]/div[2]/div/div/div/ul/li[9]/button"
                    elif page_num == 4:
                        current_next_button_xpath = "xpath://*[@id='ai_comments']/div[2]/div[4]/div[2]/div/div/div/ul/li[10]/button"
                    else: # page_num > 4
                        current_next_button_xpath = "xpath://*[@id='ai_comments']/div[2]/div[4]/div[2]/div/div/div/ul/li[11]/button"
                    
                    print(f"Page {page_num}: Attempting to find next button with dynamic XPath: {current_next_button_xpath}")
                    next_button = page.ele(current_next_button_xpath, timeout=10)
                    if next_button:
                        print(f"Page {page_num}: Next button found.")
                        if next_button.states.is_enabled:
                            print(f"Page {page_num}: Next button is enabled. Attempting to click.")
                            try:
                                print(f"Page {page_num}: Attempting ele.click(by_js=True) on next button.")
                                next_button.click(by_js=True) # User specified no wait after click, only before.
                                print(f"Page {page_num}: ele.click(by_js=True) successful.")
                                time.sleep(random.uniform(1.0, 3.5)) # Wait 1-2.5 seconds AFTER click
                            except Exception as e_click_js:
                                print(f"Page {page_num}: ele.click(by_js=True) failed: {e_click_js}. Trying page.actions click.")
                                try:
                                    page.actions.move_to(next_button).click().perform()
                                    print(f"Page {page_num}: page.actions click successful.")
                                    time.sleep(random.uniform(1.0, 2.5)) # Wait 1-2.5 seconds AFTER click
                                except Exception as e_actions_click:
                                    print(f"Page {page_num}: page.actions click also failed: {e_actions_click}. Click failed.")
                                    page_scrape_successful_this_iteration = False # If click fails, this page effectively failed to lead to next
                                    break # Stop if all click attempts fail
                        else:
                            print(f"Page {page_num}: Next button found but is NOT enabled.")
                            page_scrape_successful_this_iteration = False # Cannot proceed
                            break 
                    else:
                        print(f"Page {page_num}: Next button NOT found.")
                        page_scrape_successful_this_iteration = False # Cannot proceed
                        break 
                # else: Last page, no next button click needed.

            except Exception as e:
                print(f"Error on page {page_num}: {e}")
                page_scrape_successful_this_iteration = False
                break # Stop on critical error for a page
            finally:
                status_to_print = "success" if page_scrape_successful_this_iteration else "fail"
                print(f"Scraping page {page_num} {status_to_print}")
                if not page_scrape_successful_this_iteration and page_num < TOTAL_PAGES_TO_SCRAPE :
                    # If a page failed and it wasn't the last one, and we couldn't click next.
                    print(f"Stopping scraping due to failure on page {page_num} before reaching the end.")
                    break # Ensure we break out of the main loop

    print(f"Finished scraping. Data saved to {CSV_FILE}")
    if page:
        page.quit()

if __name__ == '__main__':
    main() 