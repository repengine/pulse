from intelligence.worldstate_loader import load_initial_state
from core.variable_registry import registry

ws = load_initial_state()           # reads baseline file
print("Missing after baseline:", registry.flag_missing_variables(ws.variables.as_dict())[:10])