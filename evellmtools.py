import json
from websocket import create_connection
from langchain.pydantic_v1 import BaseModel, Field
from langchain_core.tools import tool
from evehasstools import hass_get_todo_items, run_hass_service

from enum import Enum

class TodoList(Enum):
    TODO = "todo.todo"
    SHOPPING = "todo.shopping"

class get_todo_list_schema(BaseModel):
    """Get items from todo list"""
    todo_list: TodoList = Field(...,description="Name of to do list")

@tool
def get_todo_list(todo_list: str) -> str:
    """Get items from todo list"""
    todo_items = hass_get_todo_items(todo_list)
    return todo_items

class add_todo_item_schema(BaseModel):
    """Add item to todo list"""
    todo_list: TodoList = Field(...,description="Name of to do list")
    todo_item: str = Field(description="To do item to be added to the list")

@tool
def add_todo_item(todo_list: str, todo_item: str):
    """Add item to todo list"""
    sdata = {"item":todo_item}
    hres = run_hass_service("todo","add_item",todo_list,sdata,return_response=False)

todo_tools = [get_todo_list_schema,add_todo_item_schema]
tools_dict = {"get_todo_list_schema": get_todo_list,"add_todo_item_schema":add_todo_item}