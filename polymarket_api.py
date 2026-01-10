import requests
import time
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PolymarketAPI:
    """
    Client for interacting with Polymarket Gamma and CLOB APIs.
    """
    GAMMA_URL = "https://gamma-api.polymarket.com"
    CLOB_URL = "https://clob.polymarket.com" 

    def __init__(self):
        self.session = requests.Session()

    def get_top_markets(self, limit=20, active=True):
        """
        Fetch top markets by volume/activity from Gamma API.
        """
        try:
            params = {
                "limit": limit,
                "active": "true" if active else "false",
                "closed": "false" if active else "true",
                "order": "volume",
                "ascending": "false"
            }
            url = f"{self.GAMMA_URL}/markets"
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            markets = data if isinstance(data, list) else data.get('data', [])
            logger.info(f"API fetched {len(markets)} raw markets.")
            
            valid_markets = []
            for m in markets:
                # Handle clobTokenIds which comes as a stringified list "[...]"
                if isinstance(m.get('clobTokenIds'), str):
                    try:
                        import json 
                        m['clobTokenIds'] = json.loads(m['clobTokenIds'])
                    except Exception as e:
                        pass
                
                # Handle outcomes similarly
                if isinstance(m.get('outcomes'), str):
                    try:
                        import json
                        m['outcomes'] = json.loads(m['outcomes'])
                    except:
                        pass

                if m.get('clobTokenIds') and isinstance(m['clobTokenIds'], list):
                    valid_markets.append(m)
            
            logger.info(f"Filtered to {len(valid_markets)} valid markets with token IDs.")
            return valid_markets
        except Exception as e:
            logger.error(f"Error fetching top markets: {e}")
            return []

    def get_market_trades(self, token_id):
        """
        Fetch recent trades for a specific outcome Token ID using Data API.
        """
        try:
            DATA_API_URL = "https://data-api.polymarket.com"
            url = f"{DATA_API_URL}/trades" 
            params = {"market": token_id, "limit": 50} 
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching trades for {token_id}: {e}")
            return []

    def get_user_activity(self, user_address):
        """
        Fetch activity/trades for a user to determine account history.
        """
        try:
            DATA_API_URL = "https://data-api.polymarket.com"
            url = f"{DATA_API_URL}/activity"
            params = {"user": user_address, "limit": 50}
            
            response = self.session.get(url, params=params)
            if response.status_code == 404:
                return [] 
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error checking user {user_address}: {e}")
            return []
