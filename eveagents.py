import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from homeassistant_api import Client

load_dotenv()

hass_token = os.getenv('HASS_TOKEN')
openai_api_key = os.getenv('OPENROUTER_API_KEY')

hass_api_url = "http://192.168.2.100:8123/api"
openai_api_url = "https://openrouter.ai/api/v1"

class BaseAgent:
    def __init__(self,llm_model="openai/gpt-4o-mini"):
        self.llm_model = llm_model
        
        self.hass_token = hass_token
        self.openai_api_key = openai_api_key

        self.hass_api_url = hass_api_url
        self.openai_api_url=openai_api_url

        self.client = Client(self.hass_api_url, self.hass_token)
        self.llm = self.get_llm()
        self.sys_prompt = self.get_sys_prompt()

    def get_sys_prompt(self):
        return "You're a helpful assistant."

    def get_llm(self):
        llm = ChatOpenAI(
            model=self.llm_model,
            api_key=self.openai_api_key,
            base_url=self.openai_api_url
        )
        return llm

    def invoke(self,q: str) -> str:
        messages = [
            ("system",self.sys_prompt),
            ("human", q),
        ]
        return self.llm.invoke(messages).content

        

agent = BaseAgent()
res = agent.invoke("Hello world!")
print(res)