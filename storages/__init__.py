from .chromadb_storage import ChromaStorage
from chromadb.config import Settings
from config import config

host = config.CHROMADB_SERVER_URL

client_settings = Settings(
      is_persistent= True,
    allow_reset=True
)
path = config.SQLITE_PATH
chromadb = ChromaStorage(host, path, client_settings)
