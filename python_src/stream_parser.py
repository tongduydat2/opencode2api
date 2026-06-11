import json

class ToolCallFilter:
    def __init__(self, disable_tools=False, force_strip=False):
        self.active = disable_tools or force_strip
        self.in_block = False
        
    def filter_chunk(self, chunk: str) -> str:
        if not self.active or not chunk:
            return chunk
            
        output = ""
        remaining = chunk
        while remaining:
            if self.in_block:
                end_idx = remaining.find('</function_calls>')
                if end_idx == -1:
                    return output
                remaining = remaining[end_idx + len('</function_calls>'):]
                self.in_block = False
                continue
                
            start_idx = remaining.find('<function_calls>')
            if start_idx == -1:
                output += remaining
                return output
                
            output += remaining[:start_idx]
            remaining = remaining[start_idx + len('<function_calls>'):]
            self.in_block = True
            
        return output

class ToolCallStreamParser:
    def __init__(self):
        self.buffer = ""
        self.open_tag = "<function_calls>"
        self.close_tag = "</function_calls>"
        
    def parse_chunk(self, chunk: str) -> list:
        if not chunk:
            return []
            
        self.buffer += chunk
        parsed_calls = []
        
        while self.buffer:
            start_idx = self.buffer.find(self.open_tag)
            if start_idx == -1:
                # Keep the last open_tag.length - 1 chars just in case the tag is split across chunks
                keep_len = len(self.open_tag) - 1
                if len(self.buffer) > keep_len:
                    self.buffer = self.buffer[-keep_len:]
                break
                
            end_idx = self.buffer.find(self.close_tag, start_idx + len(self.open_tag))
            if end_idx == -1:
                self.buffer = self.buffer[start_idx:]
                break
                
            block = self.buffer[start_idx:end_idx + len(self.close_tag)]
            from .tool_runtime import parse_tool_calls_from_text
            parsed_calls.extend(parse_tool_calls_from_text(block))
            self.buffer = self.buffer[end_idx + len(self.close_tag):]
            
        return parsed_calls
