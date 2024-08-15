import os, datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from homeassistant_api import Client
from evehasstools import hass_get_todo_items
from langchain_core.messages import HumanMessage, SystemMessage
from evellmtools import cctv_tools, smart_home_tools, todo_tools, tools_dict

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
        return SystemMessage("You're a helpful assistant.")

    def get_llm(self):
        llm = ChatOpenAI(
            model=self.llm_model,
            api_key=self.openai_api_key,
            base_url=self.openai_api_url
        )
        return llm

    def invoke(self,q: str) -> str:
        messages = [self.sys_prompt,HumanMessage(q)]
        res = self.llm.invoke(messages)
        messages.append(res)
        if res.tool_calls:
            for tool_call in res.tool_calls:
                selected_tool = tools_dict[tool_call["name"].lower()]
                tool_msg = selected_tool.invoke(tool_call)
                messages.append(tool_msg)
            res = self.llm.invoke(messages)
        return res.content

class Meteorologist_Agent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.sys_prompt = self.get_sys_prompt()

    def get_sys_prompt(self):
        # Read system prompt template from file and pass to Home Assistant for rendering
        sys_prompt_template = ""
        with open("prompts/meteorologist_agent.txt") as file:
            sys_prompt_template = file.read()
        return SystemMessage(self.client.get_rendered_template(sys_prompt_template))

class CCTV_Agent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.sys_prompt = self.get_sys_prompt()
        self.get_tools()
    def get_tools(self):
        self.llm = self.llm.bind_tools(cctv_tools)

    def get_sys_prompt(self):
        sys_prompt = ""
        with open("prompts/cctv_agent.txt") as file:
            sys_prompt = file.read()
        return SystemMessage(sys_prompt)

class Smart_Home_Agent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.sys_prompt = self.get_sys_prompt()
        self.get_tools()

    def get_tools(self):
        self.llm = self.llm.bind_tools(smart_home_tools)

    def get_sys_prompt(self):
        sys_prompt = ""
        with open("prompts/smart_home_agent.txt") as file:
            sys_prompt_template = file.read()
        return SystemMessage(self.client.get_rendered_template(sys_prompt_template))

class Executive_Assistant_Agent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.sys_prompt = self.get_sys_prompt()
        self.get_tools()

    def get_tools(self):
        self.llm = self.llm.bind_tools(todo_tools)

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
        calendar_events = "none"

        # Read system prompt template from file and populate with data
        sys_prompt_template = ""
        with open("prompts/executive_assistant_agent.txt") as file:
            sys_prompt_template = file.read()
        prompt_data = {"now":now,"weather":weather,"todo_items":todo_items,"calendar_events":calendar_events}
        sys_prompt = sys_prompt_template.format(**prompt_data)
        return SystemMessage(sys_prompt)
        
