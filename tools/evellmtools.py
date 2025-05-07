"""Collection of LLM tools."""

from agents import function_tool

from evehasstools import hass_get_todo_items, run_hass_service


@function_tool
def analyze_cctv_camera(camera_id: str, prompt: str) -> str:
    """Analyze snapshot of CCTV camera.

    Args:
        camera_id: ID of the camera to be analyzed
        prompt: A prompt to describe the image based on the user query

    """
    camera_id = "camera."+camera_id
    sdata = {
        "provider": "01J49RMPVMV2H5S4T343X2QZM0",
        "model": "gpt-4o-mini",
        "max_tokens": 500,
        "temperature": 0.5,
        "message": prompt,
        "image_entity": [camera_id],
    }
    return run_hass_service("llmvision","image_analyzer",camera_id,sdata)



@function_tool
def get_todo_list(todo_list: str) -> str:
    """Get items from todo list. Use the default list if user doesn't specify a list.

    Args:
        todo_list: Name of to do list

    """
    return hass_get_todo_items(todo_list)

@function_tool
def add_todo_item(todo_list: str, todo_item: str) -> None:
    """Add item to todo list.  Use the default list if user doesn't specify a list.

    Args:
        todo_list: Name of to do list
        todo_item: Item to add to the to do list

    """
    sdata = {"item":todo_item}
    run_hass_service("todo","add_item",todo_list,sdata,return_response=False)

@function_tool
def execute_smart_home_action(domain: str, action: str, entity_id: str) -> None:
    """Execute a Smart Home action.

    Args:
        domain: The domain of the action
        action: The action to be called
        entity_id: The ID of the entity to be acted on

    """
    run_hass_service(domain,action,entity_id,return_response=False)



cctv_tools = [analyze_cctv_camera]
smart_home_tools = [execute_smart_home_action]
executive_assistant_tools = [get_todo_list,add_todo_item]
