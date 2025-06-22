#!/usr/bin/env python3
"""
Main script for running the OptiSigns Help Center Article Scraper
"""

from optisigns_scraper import OptiSignsScraper

def main():
    """Main execution function"""
    print("🚀 OptiSigns Help Center Article Scraper")
    print("=" * 50)
    
    # Create scraper instance
    scraper = OptiSignsScraper()
    
    # Run the scraper
    try:
        articles_scraped = scraper.scrape_articles(count=30)
        print(f"\n🎉 Successfully scraped {articles_scraped} articles!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")

if __name__ == "__main__":
    main() 