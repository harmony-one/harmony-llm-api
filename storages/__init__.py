from .chromadb_storage import ChromaStorage
from chromadb.config import Settings
from config import config


client_settings = Settings(
    is_persistent= True,
    allow_reset=True
)

path = config.CHROMA_SERVER_PATH
chromadb = ChromaStorage(path, client_settings)
