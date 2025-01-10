import asyncio
import json
from bs4 import BeautifulSoup
import zendriver as zd
import time

def format_number_with_commas(number):
    try:
        cleaned_number = ''.join(filter(str.isdigit, str(number)))
        if not cleaned_number:
            return "0"
        return "{:,}".format(int(cleaned_number))
    except (ValueError, TypeError):
        return "0"

async def get_population_data(page):
    try:
        content = await page.get_content()
        soup = BeautifulSoup(content, 'html.parser')
        
        def extract_counter_number(selector):
            try:
                element = soup.select_one(selector)
                if element:
                    number_parts = element.find_all('span', class_='rts-nr-int')
                    number = ''.join(part.text for part in number_parts)
                    return number if number else "0"
                return "0"
            except Exception as e:
                print(f"Error extracting number for selector {selector}: {e}")
                return "0"
        
        population_data = {
            "current_population": format_number_with_commas(extract_counter_number('.rts-counter[rel="current_population"]')),
            "births_today": format_number_with_commas(extract_counter_number('.rts-counter[rel="births_today"]')),
            "deaths_today": format_number_with_commas(extract_counter_number('.rts-counter[rel="dth1s_today"]')),
            "population_growth": format_number_with_commas(extract_counter_number('.rts-counter[rel="absolute_growth"]'))
        }
        
        top_20_countries = []
        top_20_lines = soup.select('.t20-line')
        
        for line in top_20_lines:
            try:
                rank_element = line.find('span', class_=['t20-rank', 't20-rank10'])
                country_element = line.find('span', class_='t20-country')
                population_element = line.find('span', class_='t20-number')
                
                if not all([rank_element, country_element, population_element]):
                    continue
                
                rank = rank_element.text.strip()
                country_name = country_element.text.strip()
                
                population_spans = population_element.find_all('span', class_='rts-nr-int')
                population = ''.join(span.text for span in population_spans)
                
                if not rank or not country_name or not population:
                    continue
                
                country_data = {
                    "rank": int(rank),
                    "country": country_name,
                    "population": format_number_with_commas(population)
                }
                top_20_countries.append(country_data)
            except Exception as e:
                print(f"Error processing country data: {e}")
                continue
        
        population_data['top_20_countries'] = top_20_countries
        population_data['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        print(json.dumps(population_data, indent=2))
        return True
        
    except Exception as e:
        print(f"Error during data extraction: {e}")
        return False

async def main():
    url = 'https://www.worldometers.info/world-population/'
    
    try:
        browser = await zd.start(headless=True)
        page = await browser.get(url)
        await asyncio.sleep(5)
        
        while True:
            success = await get_population_data(page)
            if success:
                await asyncio.sleep(1)
            else:
                try:
                    await page.reload()
                    await asyncio.sleep(5)
                except Exception as e:
                    print(f"Error reloading page: {e}")
                    await asyncio.sleep(5)
                    
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        await browser.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping script...")
