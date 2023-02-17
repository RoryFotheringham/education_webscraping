import argparse
from database_handler import DatabaseHandler
from mit_scraper import Scraper as MitScraper
from khan_scraper import Scraper as KhanScraper


class Crawler:
    """
    The 'mother of all scripts', this calls upon all of the Scraping files, and forms the
    parent file that can be used to re-run the whole of scraping and metadata storage.
    It does the following:
    1. Freshly re-scrape (or only look for new courses) from MIT and Khan Academy 
    2. Update the metadata database with the new scraped values
    """
    def __init__(self, num_courses, only_new_courses):
        self.scrape(num_courses, only_new_courses)
        self.update_db()

    def scrape(self, num_courses, only_new_courses):
        MitScraper(num_courses, only_new_courses)
        KhanScraper(num_courses)

    def update_db(self):
        crawler = DatabaseHandler()
        crawler.fill_db()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--count', default=1, type=int)
    parser.add_argument('-s', '--skip', default=1, type=int)
    args = parser.parse_args()

    crawler = Crawler(args.count, args.skip)