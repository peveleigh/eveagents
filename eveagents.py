import os, datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from homeassistant_api import Client
from evehasstools import hass_get_todo_items

load_dotenv()

hass_token = os.getenv('HASS_TOKEN')
openai_api_key = os.getenv('OPENROUTER_API_KEY')

hass_api_url = os.getenv('HASS_API_URL')
openai_api_url = os.getenv('OPENROUTER_API_URL')

class BaseAgent:
    def __init__(self,llm_model="openai/gpt-4o-mini"):
        self.llm_model = llm_model
        
        self.hass_token = hass_token
        self.openai_api_key = openai_api_key

        self.hass_api_url = f"http://{hass_api_url}"
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

class Meteorologist_Agent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.sys_prompt = self.get_sys_prompt()

    def get_sys_prompt(self):
        # Read system prompt template from file and pass to Home Assistant for rendering
        sys_prompt_template = ""
        with open("prompts/meteorologist_agent.txt") as file:
            sys_prompt_template = file.read()
        return self.client.get_rendered_template(sys_prompt_template)

class Executive_Assistant_Agent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.sys_prompt = self.get_sys_prompt()

    def get_sys_prompt(self):
        # Get current date and day of the week
        now = datetime.datetime.now().strftime("%A %B %d %Y")

        # Get a weather update from the meteorologist agent
        meteorologist = Meteorologist_Agent()
        weather = meteorologist.invoke("Provide a forecast summary for today. Don't mention anything but the forecast.")    

        # Get the user's to do items
        todo_items = hass_get_todo_items("todo.todo")

        # Get the user's calendar events. 
        # PLACEHOLDER FOR NOW
        calender_events = "none"

        # Read system prompt template from file and populate with data
        sys_prompt_template = ""
        with open("prompts/executive_assistant_agent.txt") as file:
            sys_prompt_template = file.read()
        sys_prompt = sys_prompt_template.format(now=now,weather=weather,todo_items=todo_items,calender_events=calender_events)
        return sys_prompt
        

agent = Executive_Assistant_Agent()
res = agent.invoke("What's on my todo list?")
print(res)
