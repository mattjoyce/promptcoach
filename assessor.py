import subprocess
import re
from pathlib import Path
from typing import Dict, Optional, Union

class PromptImprover:
    def __init__(self, fabric_path: str = "~/fabric"):
        self.fabric_path = Path(fabric_path).expanduser()

    def _run_fabric(self, input_text: str, pattern: str, cli_args: Optional[Dict[str, Union[str, bool]]] = None) -> str:
        """
        Execute fabric command with given input, pattern, and CLI arguments.
        Handles both value arguments (--key value) and switches (--flag).
        """
        command = [str(self.fabric_path), "--pattern", pattern]
        
        if cli_args:
            for key, value in cli_args.items():
                key = key if key.startswith('--') else f"--{key}"
                if isinstance(value, bool):
                    if value:  # Only add the switch if True
                        command.append(key)
                else:
                    command.extend([key, str(value)])

        try:
            process = subprocess.run(
                command,
                input=input_text,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return process.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running fabric command: {e}")
            print(f"Error output: {e.stderr}")
            raise

    def target_prompt_exec(self, 
                         content: str, 
                         target_pattern_name: str, 
                         cli_args: Optional[Dict[str, Union[str, bool]]] = None) -> str:
        """
        Execute a target prompt pattern on the given content.
        """
        formatted_input = f"{content}"
        return self._run_fabric(formatted_input, target_pattern_name, cli_args)

    def assess_prompt(self,
                     content: str,
                     target_pattern_text: str,
                     execution_result: str,
                     action_pattern_name: str,
                     cli_args: Optional[Dict[str, Union[str, bool]]] = None) -> str:
        """
        Assess the prompt execution results.
        """
        assessment_input = f"""<CONTENT>
{content}
</CONTENT>

<PROMPT_USED>
{target_pattern_text}
</PROMPT_USED>

<RESULT_FROM_PROMPT>
{execution_result}
</RESULT_FROM_PROMPT>
"""
        with open("assessment_input.txt", "w") as f:
            f.write(assessment_input)
        return self._run_fabric(assessment_input, action_pattern_name, cli_args)

    def improve_target_prompt(self,
                            target_pattern_text: str,
                            feedback: str,
                            action_pattern_name: str,
                            cli_args: Optional[Dict[str, Union[str, bool]]] = None) -> str:
        """
        Generate improved prompt based on feedback.
        """
        improvement_input = f"""<PROMPT_TO_IMPROVE>
{target_pattern_text}
</PROMPT_TO_IMPROVE>

<FEEDBACK>
{feedback}
</FEEDBACK>"""
        with open("improvement_input.txt", "w") as f:
            f.write(improvement_input)
        return self._run_fabric(improvement_input, action_pattern_name, cli_args)

def ensure_unique_path(base_path: str, mkdir: bool = True) -> Path:
    path = Path(base_path)
    
    # If path exists, increment with .1, .2, etc.
    if path.exists():
        counter = 1
        while True:
            new_path = path.with_name(f"{path.name}.{counter}")
            if not new_path.exists():
                path = new_path
                break
            counter += 1

    if mkdir:
        path.mkdir(parents=True, exist_ok=True)
    
    return path

def separate_string(source: str, token1: str, token2: str):
    # Create regex patterns to extract content between the provided tokens
    pattern1 = f"<\s*{token1}\s*>(.*?)<\s*/\s*{token1}\s*>"
    pattern2 = f"<\s*{token2}\s*>(.*?)<\s*/\s*{token2}\s*>"
    
    # Extract the content using regex search
    match1 = re.search(pattern1, source, re.DOTALL)
    match2 = re.search(pattern2, source, re.DOTALL)
    
    # Extract text or use empty string if no match is found
    this = match1.group(1).strip() if match1 else ""
    that = match2.group(1).strip() if match2 else ""
    
    return this, that

def main():
    # Example usage with both types of CLI arguments
    improver = PromptImprover()
    
    # chnage this to the content
    with open("content-is-king.txt", "r") as f:
        content = f.read()

    project_name = "mistral"
    save = True
    if save:
        save_path = ensure_unique_path(f"/home/matt/promptcoach/{project_name}", mkdir=True)
        print(f"Saving project to {save_path}")

    fabric_path = "/home/matt/.config/fabric"
    target_pattern_name = "extract_insights"
    target_pattern_text = open(f"{fabric_path}/patterns/{target_pattern_name}/system.md", "r").read()
    assessor_pattern_name = "rate_ai_result"
    improve_pattern_name = "improve_prompt_with_feedback"


    # Example CLI arguments including switches
    assesor_cli_args = {
        "model": "o1-preview",
        "raw": True,              
    }

    student_cli_args = {
        "model": "mistral:latest",
    }
    
    try:
        result = improver.target_prompt_exec(
            content=content,
            target_pattern_name=target_pattern_name,
            cli_args=student_cli_args
        )
        print("\n=== Execution Result ===")
        print(result)
        if save:
            with open(f"{save_path}/result.txt", "w") as f:
                f.write(result)

        
        feedback = improver.assess_prompt(
            content=content,
            target_pattern_text=target_pattern_text,
            execution_result=result,
            action_pattern_name=assessor_pattern_name,
            cli_args=assesor_cli_args
        )
        print("\n=== Assessment Feedback ===")
        print(feedback)
        if save:
            with open(f"{save_path}/feedback.txt", "w") as f:
                f.write(feedback)
        
        new_prompt = improver.improve_target_prompt(
            target_pattern_text=target_pattern_text,
            feedback=feedback,
            action_pattern_name=improve_pattern_name,
            cli_args=assesor_cli_args
        )
        print("\n=== Improved Prompt ===")
        print(new_prompt)
        if save:
            prompt, comentary = separate_string(new_prompt,"IMPROVED_PROMPT","COMMENTARY")
            with open(f"{save_path}/improved_prompt.txt", "w") as f:
                f.write(prompt)
            with open(f"{save_path}/commentary.txt", "w") as f:
                f.write(comentary)
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()