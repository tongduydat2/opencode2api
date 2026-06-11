import re
import json

def strip_function_call_markup(text: str, strip_whitespace: bool = True) -> str:
    """Removes `<function_calls>...</function_calls>` blocks from text."""
    if not text:
        return text
    # Non-greedy match for function_calls blocks
    pattern = re.compile(r'<function_calls>.*?</function_calls>', re.IGNORECASE | re.DOTALL)
    stripped = pattern.sub('', text)
    return stripped.strip() if strip_whitespace else stripped

def parse_tool_calls_from_text(text: str):
    """
    Parses OpenCode XML-like tool calls:
    <function_calls>[{"name": "...", "arguments": {...}}]</function_calls>
    or single object:
    <function_calls>{"name": "...", "arguments": {...}}</function_calls>
    """
    if not text:
        return []
        
    pattern = re.compile(r'<function_calls>(.*?)</function_calls>', re.IGNORECASE | re.DOTALL)
    matches = pattern.findall(text)
    
    tool_calls = []
    for match in matches:
        content = match.strip()
        if not content:
            continue
        try:
            parsed = json.loads(content)
            if isinstance(parsed, list):
                tool_calls.extend(parsed)
            elif isinstance(parsed, dict):
                tool_calls.append(parsed)
        except json.JSONDecodeError:
            pass
            
    # Format to Claude ToolUse blocks
    # Claude ToolUse expects: { "type": "tool_use", "id": "...", "name": "...", "input": {...} }
    # OpenCode outputs: { "name": "...", "arguments": {...} }
    # Since we assign IDs to tool uses in Anthropic, we'll generate one if none.
    import uuid
    
    claude_tool_uses = []
    for tc in tool_calls:
        if "name" in tc:
            claude_tool_uses.append({
                "type": "tool_use",
                "id": f"toolu_{uuid.uuid4().hex[:12]}",
                "name": tc["name"],
                "input": tc.get("arguments", {})
            })
            
    return claude_tool_uses

def build_external_tool_registry(tools: list) -> dict:
    """
    Builds a registry mapping external tool names to their schema.
    Anthropic tool schema: { "name": "...", "description": "...", "input_schema": {...} }
    """
    registry = {}
    if not tools:
        return registry
        
    for t in tools:
        name = t.get("name")
        if name:
            registry[name] = t
            
    return registry

def generate_tool_instructions(tools: list) -> str:
    """
    If tools are provided, OpenCode needs instructions to output <function_calls>.
    """
    if not tools:
        return ""
        
    tool_defs = []
    for t in tools:
        tool_defs.append(json.dumps({
            "name": t.get("name"),
            "description": t.get("description", ""),
            "parameters": t.get("input_schema", {})
        }))
        
    prompt = (
        "You have access to the following tools:\n"
        f"[{', '.join(tool_defs)}]\n\n"
        "To use a tool, respond ONLY with a JSON object or array inside a <function_calls> block. "
        "For example: <function_calls>{\"name\": \"tool_name\", \"arguments\": {\"arg1\": \"value\"}}</function_calls>\n"
        "Do not include any other text when calling a tool."
    )
    return prompt
