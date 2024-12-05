import os
from dotenv import load_dotenv

load_dotenv()

def generate_new_secret_key():
    key = os.urandom(24).hex()
    return key
class Config(object):
    ENV=os.environ.get('ENV') if os.environ.get('ENV') else 'production'
    DEBUG = os.environ.get('DEBUG') if os.environ.get('DEBUG') else True
    TESTING = os.getenv('TESTING') if os.environ.get('DEBUG') else True
    MAX_WORKERS = 10
    SECRET_KEY = generate_new_secret_key()
    CHROMADB_SERVER_URL = os.getenv('CHROMADB_SERVER_URL')
    CHROMA_SERVER_PATH = os.getenv('CHROMA_SERVER_PATH') if os.getenv('CHROMA_SERVER_PATH') else "/app/data/chroma"
    OPENAI_MODEL = os.getenv('OPENAI_MODEL') if os.getenv('OPENAI_MODEL') else "gpt-3.5-turbo"
    OPENAI_MAX_TOKENS = os.getenv('OPENAI_MAX_TOKENS') if os.getenv('OPENAI_MAX_TOKENS') else 600
    WEB_CRAWLER_HTTP = os.environ.get('WEB_CRAWLER_HTTP')
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    API_KEYS = os.environ.get("API_KEYS").split(',') if os.environ.get("API_KEYS") else []
    LUMAAI_API_KEY = os.environ.get("LUMAAI_API_KEY")
    TELEGRAM_API_KEY = os.environ.get('TELEGRAM_API_KEY')
    XAI_API_KEY = os.getenv("XAI_API_KEY")
    TELEGRAM_REPORT_ID = os.environ.get('TELEGRAM_REPORT_ID') # telegram user id
    WEB3_PROVIDER_URL = 'https://api.harmony.one'
    JWT_EXPIRATION_MINUTES = 30
    REFRESH_EXPIRATION_DAYS = 7
config = Config()
