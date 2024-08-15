import json
from websocket import create_connection
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool
from evehasstools import hass_get_todo_items, run_hass_service

from enum import Enum
from typing import Dict

class TodoList(Enum):
    TODO = "todo.todo"
    SHOPPING = "todo.shopping"

class get_todo_list(BaseModel):
    """Get items from todo list"""
    todo_list: TodoList = Field(...,description="Name of to do list")

@tool
def get_todo_list_func(todo_list: str) -> str:
    """Get items from todo list"""
    todo_items = hass_get_todo_items(todo_list)
    return todo_items

class add_todo_item(BaseModel):
    """Add item to todo list"""
    todo_list: TodoList = Field(...,description="Name of to do list")
    todo_item: str = Field(description="To do item to be added to the list")

@tool
def add_todo_item_func(todo_list: str, todo_item: str):
    """Add item to todo list"""
    sdata = {"item":todo_item}
    hres = run_hass_service("todo","add_item",todo_list,sdata,return_response=False)

class ActionData(BaseModel):
    entity_id: str = Field(...,description="The entity_id of the device that will be acted upon. It must start with domain, followed by dot character.")

class execute_smart_home_action(BaseModel):
    """Execute a Smart Home action"""
    domain: str = Field(...,description="The domain of the action")
    action: str = Field(...,description="The action to be called")
    action_data: ActionData = Field(...,description="The service data object to indicate what to control.")

@tool
def execute_smart_home_action_func(domain: str, action: str, action_data: Dict):
    """Execute a Smart Home action"""
    res = run_hass_service(domain,action,action_data["entity_id"],return_response=False)

smart_home_tools = [execute_smart_home_action]
todo_tools = [get_todo_list,add_todo_item]
tools_dict = {
    "get_todo_list": get_todo_list_func,
    "add_todo_item":add_todo_item_func,
    "execute_smart_home_action":execute_smart_home_action_func
    }