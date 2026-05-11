import time
import re
from playwright.sync_api import sync_playwright

def scrape_google_maps(keyword: str, city: str, max_results: int = 30) -> list[dict]:
    """
    Scrape Google Maps for business leads.
    Returns a list of dicts with keys:
      name, phone, address, rating, reviews, website, category
    """
    query = f"{keyword} in {city}"
    url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"

    results = []
    seen_entities = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = context.new_page()

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)

            # Dismiss any cookie/consent dialogs
            try:
                accept_btn = page.locator("button:has-text('Accept all'), button:has-text('I agree')")
                if accept_btn.count() > 0:
                    accept_btn.first.click()
                    time.sleep(1)
            except Exception:
                pass

            # Wait for the results panel
            page.wait_for_selector("div[role='feed']", timeout=15000)

            # Scroll the results panel to load listings
            feed = page.locator("div[role='feed']")
            for _ in range(10):
                feed.evaluate("el => el.scrollBy(0, 1200)")
                time.sleep(1.2)

            # Collect all unique listing URLs
            links = page.locator("div[role='feed'] > div > div > a")
            urls = []
            for i in range(links.count()):
                href = links.nth(i).get_attribute("href")
                if href and href not in urls:
                    urls.append(href)
                if len(urls) >= max_results:
                    break

            for link in urls:
                try:
                    page.goto(link, wait_until="domcontentloaded", timeout=20000)
                    time.sleep(2)

                    # --- Name ---
                    name = ""
                    try:
                        name = page.locator("h1.DUwDvf, h1[class*='fontHeadlineLarge']").first.inner_text(timeout=4000)
                    except Exception:
                        pass

                    # --- Phone ---
                    phone = ""
                    try:
                        phone_el = page.locator("[data-item-id*='phone:tel:'] .Io6YTe")
                        if phone_el.count() > 0:
                            phone = phone_el.first.inner_text(timeout=3000)
                        else:
                            phone_text = page.locator("button[data-tooltip='Copy phone number'] .Io6YTe")
                            if phone_text.count() > 0:
                                phone = phone_text.first.inner_text(timeout=3000)
                    except Exception:
                        pass

                    # Deduplication check
                    identity = f"{name.strip()}|{phone.strip()}"
                    if not name or identity in seen_entities:
                        continue
                    seen_entities.add(identity)

                    # --- Category ---
                    category = ""
                    try:
                        category = page.locator("button[jsaction*='category'], .DkEaL").first.inner_text(timeout=3000)
                    except Exception:
                        pass

                    # --- Address ---
                    address = ""
                    try:
                        address_el = page.locator("[data-item-id='address'] .Io6YTe")
                        if address_el.count() > 0:
                            address = address_el.first.inner_text(timeout=3000)
                    except Exception:
                        pass

                    # --- Website ---
                    website = ""
                    try:
                        website_el = page.locator("[data-item-id='authority'] .Io6YTe")
                        if website_el.count() > 0:
                            website = website_el.first.inner_text(timeout=3000)
                    except Exception:
                        pass

                    # --- Rating ---
                    rating = ""
                    try:
                        rating = page.locator("div.F7nice span[aria-hidden='true']").first.inner_text(timeout=3000)
                    except Exception:
                        pass

                    # --- Reviews ---
                    reviews = ""
                    try:
                        rev_el = page.locator("div.F7nice span[aria-label*='review']")
                        if rev_el.count() > 0:
                            rev_text = rev_el.first.get_attribute("aria-label", timeout=3000) or ""
                            nums = re.findall(r"[\d,]+", rev_text)
                            reviews = nums[0] if nums else ""
                    except Exception:
                        pass

                    results.append({
                        "Name": name.strip(),
                        "Category": category.strip(),
                        "Phone": phone.strip(),
                        "Address": address.strip(),
                        "Rating": rating.strip(),
                        "Reviews": reviews.strip(),
                        "Website": website.strip(),
                    })

                except Exception:
                    continue

        except Exception as e:
            print(f"[Scraper Error] {e}")
        finally:
            browser.close()

    return results
