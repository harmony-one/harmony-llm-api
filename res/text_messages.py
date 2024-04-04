class EngMsg():
    
    TEMP_PDF_INQUIRY_RESPONSE = """Certainly! To improve your CV, tailor it to the job description by emphasizing relevant experiences and skills, 
quantify achievements to demonstrate impact (e.g., increased sales by 20%), and include industry-specific keywords to 
pass applicant tracking systems and highlight expertise."""
    OPTIONAL = '(Optional) '
    REQUIRED = '(Required) '
    
    API_NAMESPACE_VERTEX_DESCRIPTION = 'Google Vertex/Palm2 APIs'
    API_NAMESPACE_LLMS_DESCRIPTION = 'LLMs APIs'
    API_NAMESPACE_OPENAI_DESCRIPTION = 'OpenAI APIs'
    API_NAMESPACE_ANTHROPIC_DESCRIPTION = 'Claude APIs'

    API_DOC_PARAMS_COLLECTION_NAME = 'Collection Name'
    API_DOC_PARAMS_DATA = 'Audio file'
    API_DOC_PARAMS_PDF_ISOLATE = 'PDF file (required)'
    API_DOC_PARAMS_PDF = 'PDF file (required if no URL is provided)'
    API_DOC_PARAMS_URL = 'PDF file URL (required if no PDF is provided)'
    API_DOC_PARAMS_SYSTEM = 'Completion context (default "Summarize this text")'
    API_DOC_PARAMS_MODEL = 'Completion model (default claude-3-opus-20240229)'
    API_DOC_PARAMS_MAX_TOKENS = 'Completion max tokens (default 1024)'
    API_DOC_PARAMS_JOB_DESCRIPTION = 'Job description (required)'