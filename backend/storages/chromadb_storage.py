
from llama_index.core import Document, VectorStoreIndex, ServiceContext, PromptHelper
# from llama_index.core.llms. import LLMPredictor
from llama_index.vector_stores.chroma.base import ChromaVectorStore
from llama_index.core.storage import StorageContext
import chromadb
from chromadb.config import Settings
import hashlib
from langchain.chat_models import ChatOpenAI
from config import config
class ChromaStorage:

    def __init__(self, path, settings: Settings):
        self.path = path
        self.db = chromadb.HttpClient(host=config.CHROMADB_SERVER_URL, port='8000')

    def get_path(self):
        return self.path
        
    def get_llms(self):
        llm_predictor = LLMPredictor(llm=ChatOpenAI(
        temperature=0, 
        model_name=config.OPENAI_MODEL, 
        max_tokens=config.OPENAI_MAX_TOKENS))
        service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor, system_prompt='in 20 words')
        return service_context

    
    def get_collection_name(self, chat_id, url):
        hashed = hashlib.md5(url.encode()).hexdigest()
        if not hashed[0].isalnum():
            hashed = 'a' + hashed[1:]
        if not hashed[-1].isalnum():
            hashed = hashed[:-1] + 'a'
        valid_characters = ''.join(c for c in hashed if c.isalnum() or c in ('_', '-'))
        return f"chat{chat_id}-{valid_characters}"


    def get_existing_collection(self, collection_name):
        try:
            collection = self.db.get_collection(collection_name)
            return collection
        except ValueError as e:
            return None
    
    def get_collection(self, collection_name):
        collection = self.db.create_collection(name=collection_name, get_or_create=True)
        return collection
    
    def store_text_array_from_url(self, text_array, collection_name): 
        collection = self.get_collection(collection_name)
        documents = [Document(text=t) for t in text_array.get('urlText')]
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store)
        service_context = self.get_llms()
        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, service_context=service_context)

    
    def store_text_array(self, text_array, collection_name):
        collection = self.get_collection(collection_name)
        documents = [Document(text=t) for t in text_array]
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store)
        service_context = self.get_llms()
        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, service_context=service_context)


    def get_vector_index(self, collection_name):
        collection = self.get_collection(collection_name)
        if (collection.count() > 0):
            vector_store = ChromaVectorStore(chroma_collection=collection)
            index = VectorStoreIndex.from_vector_store(
                vector_store)
            return index
        return None
    
    def delete_collection(self, collection_name):
        self.db.delete_collection(collection_name)

    def reset_database(self):
        return self.db.reset()
    