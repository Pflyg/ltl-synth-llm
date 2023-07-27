import vertexai
from vertexai.preview.language_models import CodeChatModel

vertexai.init(project="rg-finkbeiner-30141001", location="us-central1")
chat_model = CodeChatModel.from_pretrained("codechat-bison@001")
parameters = {
    "temperature": 0.5,
    "max_output_tokens": 1024
}
chat = chat_model.start_chat()