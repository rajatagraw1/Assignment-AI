import requests
import json
import os
import time
from urllib.parse import urlparse
from pathlib import Path
import argparse

class ImageScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def create_directory(self, path):
        """Create directory if it doesn't exist"""
        Path(path).mkdir(parents=True, exist_ok=True)
        
    def download_image(self, url, filepath):
        """Download image from URL"""
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False
            
    def scrape_pixabay(self, api_key, query, count=20, category="all"):
        """Scrape images from Pixabay API"""
        print(f"Scraping Pixabay for: {query}")
        
        url = "https://pixabay.com/api/"
        params = {
            'key': api_key,
            'q': query,
            'image_type': 'photo',
            'orientation': 'all',
            'category': category,
            'min_width': 1920,
            'min_height': 1080,
            'per_page': min(count, 200),
            'safesearch': 'true'
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            download_dir = f"pixabay_{query.replace(' ', '_')}"
            self.create_directory(download_dir)
            
            downloaded = 0
            for i, img in enumerate(data['hits']):
                if downloaded >= count:
                    break
                    
                img_url = img['largeImageURL']
                filename = f"pixabay_{query}_{i+1}.jpg"
                filepath = os.path.join(download_dir, filename)
                
                if self.download_image(img_url, filepath):
                    print(f"Downloaded: {filename}")
                    downloaded += 1
                    
                    # Save metadata
                    metadata = {
                        'source': 'pixabay',
                        'tags': img['tags'],
                        'user': img['user'],
                        'views': img['views'],
                        'downloads': img['downloads'],
                        'url': img['pageURL']
                    }
                    
                    with open(filepath.replace('.jpg', '_metadata.json'), 'w') as f:
                        json.dump(metadata, f, indent=2)
                
                time.sleep(0.5)  # Rate limiting
                
            print(f"Downloaded {downloaded} images from Pixabay")
            
        except Exception as e:
            print(f"Error scraping Pixabay: {e}")
            
    def scrape_unsplash(self, api_key, query, count=20):
        """Scrape images from Unsplash API"""
        print(f"Scraping Unsplash for: {query}")
        
        url = "https://api.unsplash.com/search/photos"
        headers = {'Authorization': f'Client-ID {api_key}'}
        
        try:
            per_page = min(count, 30)
            pages_needed = (count + per_page - 1) // per_page
            
            download_dir = f"unsplash_{query.replace(' ', '_')}"
            self.create_directory(download_dir)
            
            downloaded = 0
            for page in range(1, pages_needed + 1):
                params = {
                    'query': query,
                    'page': page,
                    'per_page': per_page,
                    'orientation': 'landscape'
                }
                
                response = self.session.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                for i, img in enumerate(data['results']):
                    if downloaded >= count:
                        break
                        
                    img_url = img['urls']['full']
                    filename = f"unsplash_{query}_{downloaded+1}.jpg"
                    filepath = os.path.join(download_dir, filename)
                    
                    if self.download_image(img_url, filepath):
                        print(f"Downloaded: {filename}")
                        downloaded += 1
                        
                        # Save metadata
                        metadata = {
                            'source': 'unsplash',
                            'description': img.get('alt_description', ''),
                            'photographer': img['user']['name'],
                            'likes': img['likes'],
                            'url': img['links']['html']
                        }
                        
                        with open(filepath.replace('.jpg', '_metadata.json'), 'w') as f:
                            json.dump(metadata, f, indent=2)
                    
                    time.sleep(0.5)
                    
                if downloaded >= count:
                    break
                    
            print(f"Downloaded {downloaded} images from Unsplash")
            
        except Exception as e:
            print(f"Error scraping Unsplash: {e}")
            
    def scrape_flickr(self, api_key, query, count=20, license_type="4,5,6,7,8,9,10"):
        """Scrape images from Flickr API with Creative Commons licenses"""
        print(f"Scraping Flickr for: {query}")
        
        search_url = "https://api.flickr.com/services/rest/"
        params = {
            'method': 'flickr.photos.search',
            'api_key': api_key,
            'text': query,
            'license': license_type,  # Creative Commons licenses
            'media': 'photos',
            'per_page': min(count, 500),
            'page': 1,
            'format': 'json',
            'nojsoncallback': 1,
            'extras': 'url_o,url_l,url_c,tags,views,description,license,owner_name',
            'sort': 'relevance'
        }
        
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['stat'] != 'ok':
                print(f"Flickr API error: {data.get('message', 'Unknown error')}")
                return
                
            download_dir = f"flickr_{query.replace(' ', '_')}"
            self.create_directory(download_dir)
            
            downloaded = 0
            photos = data['photos']['photo']
            
            for photo in photos:
                if downloaded >= count:
                    break
                    
                # Try to get the best quality image URL
                img_url = None
                if 'url_o' in photo:  # Original size
                    img_url = photo['url_o']
                elif 'url_l' in photo:  # Large size
                    img_url = photo['url_l']
                elif 'url_c' in photo:  # Medium size
                    img_url = photo['url_c']
                else:
                    # Construct URL manually
                    img_url = f"https://live.staticflickr.com/{photo['server']}/{photo['id']}_{photo['secret']}_b.jpg"
                
                if img_url:
                    filename = f"flickr_{query}_{downloaded+1}.jpg"
                    filepath = os.path.join(download_dir, filename)
                    
                    if self.download_image(img_url, filepath):
                        print(f"Downloaded: {filename} by {photo.get('ownername', 'Unknown')}")
                        downloaded += 1
                        
                        # License mapping
                        license_map = {
                            '4': 'CC BY 2.0',
                            '5': 'CC BY-SA 2.0',
                            '6': 'CC BY-ND 2.0',
                            '7': 'CC BY-NC 2.0',
                            '8': 'CC BY-NC-SA 2.0',
                            '9': 'CC BY-NC-ND 2.0',
                            '10': 'Public Domain'
                        }
                        
                        # Save metadata
                        metadata = {
                            'source': 'flickr',
                            'title': photo.get('title', ''),
                            'description': photo.get('description', {}).get('_content', '') if isinstance(photo.get('description'), dict) else photo.get('description', ''),
                            'photographer': photo.get('ownername', ''),
                            'tags': photo.get('tags', ''),
                            'views': photo.get('views', 0),
                            'license': license_map.get(str(photo.get('license', '')), 'Unknown'),
                            'url': f"https://www.flickr.com/photos/{photo['owner']}/{photo['id']}/",
                            'flickr_id': photo['id']
                        }
                        
                        with open(filepath.replace('.jpg', '_metadata.json'), 'w') as f:
                            json.dump(metadata, f, indent=2)
                
                time.sleep(0.5)  # Rate limiting
                
            print(f"Downloaded {downloaded} images from Flickr")
            
        except Exception as e:
            print(f"Error scraping Flickr: {e}")
            
    def scrape_nasa_images(self, query, count=20):
        """Scrape images from NASA Image and Video Library"""
        print(f"Scraping NASA for: {query}")
        
        search_url = "https://images-api.nasa.gov/search"
        params = {
            'q': query,
            'media_type': 'image',
            'page_size': min(count, 100)
        }
        
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            download_dir = f"nasa_{query.replace(' ', '_')}"
            self.create_directory(download_dir)
            
            downloaded = 0
            for item in data['collection']['items']:
                if downloaded >= count:
                    break
                    
                # Get image details
                asset_url = item['href']
                asset_response = self.session.get(asset_url)
                asset_data = asset_response.json()
                
                # Find the largest image
                image_url = None
                for asset in asset_data:
                    if asset.endswith(('.jpg', '.jpeg', '.png')):
                        image_url = asset
                        break
                
                if image_url:
                    filename = f"nasa_{query}_{downloaded+1}.jpg"
                    filepath = os.path.join(download_dir, filename)
                    
                    if self.download_image(image_url, filepath):
                        print(f"Downloaded: {filename}")
                        downloaded += 1
                        
                        # Save metadata
                        item_data = item['data'][0]
                        metadata = {
                            'source': 'nasa',
                            'title': item_data.get('title', ''),
                            'description': item_data.get('description', ''),
                            'date_created': item_data.get('date_created', ''),
                            'center': item_data.get('center', ''),
                            'keywords': item_data.get('keywords', [])
                        }
                        
                        with open(filepath.replace('.jpg', '_metadata.json'), 'w') as f:
                            json.dump(metadata, f, indent=2)
                
                time.sleep(0.5)
                
            print(f"Downloaded {downloaded} images from NASA")
            
        except Exception as e:
            print(f"Error scraping NASA: {e}")
            
    def scrape_classical_art(self, count=20):
        """Scrape classical art from Metropolitan Museum API"""
        print("Scraping classical art from Met Museum")
        
        # Search for paintings
        search_url = "https://collectionapi.metmuseum.org/public/collection/v1/search"
        params = {
            'hasImages': 'true',
            'medium': 'Paintings',
            'q': 'classical'
        }
        
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            download_dir = "classical_art"
            self.create_directory(download_dir)
            
            downloaded = 0
            object_ids = data['objectIDs'][:count*2]  # Get more IDs in case some don't have images
            
            for obj_id in object_ids:
                if downloaded >= count:
                    break
                    
                # Get object details
                obj_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{obj_id}"
                obj_response = self.session.get(obj_url)
                obj_data = obj_response.json()
                
                if obj_data.get('primaryImage'):
                    img_url = obj_data['primaryImage']
                    title = obj_data.get('title', f'artwork_{obj_id}')
                    # Clean filename
                    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"met_{safe_title[:50]}_{downloaded+1}.jpg"
                    filepath = os.path.join(download_dir, filename)
                    
                    if self.download_image(img_url, filepath):
                        print(f"Downloaded: {filename}")
                        downloaded += 1
                        
                        # Save metadata
                        metadata = {
                            'source': 'met_museum',
                            'title': obj_data.get('title', ''),
                            'artist': obj_data.get('artistDisplayName', ''),
                            'date': obj_data.get('objectDate', ''),
                            'medium': obj_data.get('medium', ''),
                            'culture': obj_data.get('culture', ''),
                            'url': obj_data.get('objectURL', '')
                        }
                        
                        with open(filepath.replace('.jpg', '_metadata.json'), 'w') as f:
                            json.dump(metadata, f, indent=2)
                
                time.sleep(1)  # Be respectful to Met's API
                
            print(f"Downloaded {downloaded} classical artworks")
            
        except Exception as e:
            print(f"Error scraping classical art: {e}")

def main():
    parser = argparse.ArgumentParser(description='Scrape public domain images')
    parser.add_argument('--pixabay-key', help='Pixabay API key')
    parser.add_argument('--unsplash-key', help='Unsplash API key')
    parser.add_argument('--flickr-key', help='Flickr API key')
    parser.add_argument('--query', default='nature', help='Search query')
    parser.add_argument('--count', type=int, default=20, help='Number of images to download')
    parser.add_argument('--source', choices=['pixabay', 'unsplash', 'flickr', 'nasa', 'classical', 'all'], 
                       default='all', help='Image source')
    
    args = parser.parse_args()
    
    scraper = ImageScraper()
    
    if args.source in ['pixabay', 'all'] and args.pixabay_key:
        scraper.scrape_pixabay(args.pixabay_key, args.query, args.count)
        
    if args.source in ['unsplash', 'all'] and args.unsplash_key:
        scraper.scrape_unsplash(args.unsplash_key, args.query, args.count)
        
    if args.source in ['flickr', 'all'] and args.flickr_key:
        scraper.scrape_flickr(args.flickr_key, args.query, args.count)
        
    if args.source in ['nasa', 'all']:
        scraper.scrape_nasa_images(args.query, args.count)
        
    if args.source in ['classical', 'all']:
        scraper.scrape_classical_art(args.count)

if __name__ == "__main__":
    # Example usage without command line args
    scraper = ImageScraper()
    
    # You'll need to get API keys from:
    # Pixabay: https://pixabay.com/api/docs/
    # Unsplash: https://unsplash.com/developers
    
    PIXABAY_API_KEY = "50655353-bc770e26eaee44f55cfd03a5a"
    UNSPLASH_API_KEY = "jigUqqvoDXDVj74Fcm6DLbXkIJRDUIhS2eINNUBS6F0"
    FLICKR_API_KEY = ""
    
    # Example scraping calls
    scraper.scrape_pixabay(PIXABAY_API_KEY, "nature", 10)
    scraper.scrape_unsplash(UNSPLASH_API_KEY, "landscape", 10)
    scraper.scrape_flickr(FLICKR_API_KEY, "photography", 10)
    scraper.scrape_nasa_images("space", 10)
    scraper.scrape_classical_art(10)