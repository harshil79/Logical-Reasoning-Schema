# !pip3 install clingo
# !pip3 install vertexai
# import ssl
# print(ssl.OPENSSL_VERSION)

import vertexai
from vertexai.preview.language_models import ChatModel, InputOutputTextPair, TextGenerationModel
from google.oauth2 import service_account
# connect to vertex ai, to be replaced with the respective account credentials
mycredentials = service_account.Credentials.from_service_account_file('aerial-grid-415517-361a194b7eef.json')
vertexai.init(project='aerial-grid-415517', location='europe-west1', credentials=mycredentials)
import clingo
import re

def add_argument(file, argument):
    with open(file, 'r') as f:
        prompt = f.read()
        prompt_with_argument = prompt.replace("!!!!!!!!!!!!!!!!!!!!", argument)
        return prompt_with_argument
    
def copy_file_content(original_file, new_file):
    with open(original_file, 'r') as src:
        content = src.read()
    with open(new_file, 'w') as dst:
        dst.write(content)

def convert_number_to_words(s):
    num_words = {
        '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
        '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
    }
    # Replace each digit individually
    return ''.join(num_words.get(char, char) for char in s)

def replace_spaces_with_underscores_in_identifiers(s):
    # Precompile regular expression patterns for performance
    pattern_identifier = re.compile(r'\b([a-z_][a-z0-9_]*)\s+([a-z0-9_]+)\b', re.IGNORECASE)
    
    # Replace spaces between words that are likely part of an identifier with underscores
    def repl(m):
        return m.group(1) + '_' + m.group(2)

    # Apply the replacement repeatedly until no further replacements are made
    while True:
        s_new = pattern_identifier.sub(repl, s)
        if s_new == s:
            break
        s = s_new

    return s

def remove_unnecessary_characters(s):
    # First, remove specified unnecessary characters, keeping the dash to handle it separately
    s = re.sub(r'[\'`*<>~%$‘’"é£á^&#ē|@ü+/]', '', s)
    # Replace "-" with "_", but avoid replacing it within " :- "
    # This uses a negative lookbehind and lookahead to ensure we don't replace dashes in " :- "
    s = re.sub(r'(?<!:)-', '_', s)  # Replace "-" with "_" if "-" is not immediately preceded by ":"
    s = re.sub(r'-(?! )', '_', s)  # Replace "-" with "_" if "-" is not immediately followed by a space, handling the case after ":-"
    
    return s

def remove_all_but_final_period(line):
    # Temporarily replace ":-" with a placeholder
    placeholder = "TEMP_COLON_HYPHEN"
    line = line.replace(':-', placeholder)

    # Remove all periods except the final one if it exists
    parts = line.rsplit('.', 1)
    if len(parts) == 2:
        line = parts[0].replace('.', '') + '.' + parts[1]
    else:
        line = parts[0].replace('.', '')

    # Restore ":-"
    line = line.replace(placeholder, ':-')
    return line

def filter_equals_except_special_cases(s):
    # This approach tries to preserve "=" in logical expressions and assignments
    # by focusing on removing "=" only when it seems to be used in a context that
    # should be filtered out, without a clear-cut method to distinguish all cases accurately.

    # Remove "=" only if it's not clearly part of an assignment or comparison
    # The regex below is an example and might need adjustments
    # It assumes "=" to remove is surrounded by words (identifiers) without spaces
    # This might not cover all cases and could remove "=" in unintended contexts
    s = re.sub(r'(?<=[a-zA-Z0-9_])=(?=[a-zA-Z0-9_])', '', s)
    return s

def filter_colons_except_negations(s):
    # This replaces ":" with "" only if it's not followed by "-", effectively removing colons that are not part of ":-"
    s = re.sub(r':(?!\-)', '', s)
    return s

def filter_asp_code(asp_code):
    filtered_lines = []
    seen_lines = set()
    allowed_prefixes_pattern = re.compile(r'\b(neg|pos|relation)\(')

    for line in asp_code.split('\n'):
        # Add the processed line to the set of seen lines
        seen_lines.add(line)
        # Remove Non ASP code parts and special character
        if re.match(r'^\*\*|```asp', line):
            continue
        # Skip lines based on the new condition for the presence of "not"
        if re.search(r'\bnot\b', line):
            continue 

        # Remove lines not in ASP format
        if not re.match(r'^[a-zA-Z0-9_].*', line):
            continue
        # Convert all numeric digits to their corresponding words
        line = convert_number_to_words(line)
        # Replace spaces with underscores in identifiers
        line = replace_spaces_with_underscores_in_identifiers(line)
        # remove lines with the word section in it
        if "section" in line.lower():
            continue
        if not "." in line.lower():
            continue
        if not allowed_prefixes_pattern.search(line):  # Skip lines not matching the allowed patterns
            continue
        # # Delete incomplete sentences
        # if not re.search(r'\)$', line):
        #     continue
        # Add missing full stops
        if not re.search(r'\.$', line) and re.search(r'\)$', line):
            line += '.'
        # Remove dots between words
        line = re.sub(r'(?<=\w)\.(?=\w)', '', line)
        # remove ! between words
        line = re.sub(r'(?<=\w)\!(?=\w)', '', line)
        # remove special characters
        line = remove_unnecessary_characters(line)
        # Lowercase conversion while keeping ASP keywords or variables intact
        line = re.sub(r'(?<![A-Z])([A-Z]+)(?![A-Z])', lambda x: x.group(1).lower(), line)
        # Ensure only the final period is kept
        line = remove_all_but_final_period(line) 
        line = filter_colons_except_negations(line)
        line = filter_equals_except_special_cases(line)
        # Replace spaces with underscores in identifiers
        line = replace_spaces_with_underscores_in_identifiers(line)
        # line = filter_equals_except_special_cases(line) 
        filtered_lines.append(line)
    return '\n'.join(filtered_lines)
        

def apply_filter_to_asp_code(asp_code_file, output_file):
    with open(asp_code_file, 'r') as file:
        asp_code = file.read()

    filtered_code = filter_asp_code(asp_code)

    with open(output_file, 'w') as file:
        file.write(filtered_code)
    
    print(f"Filtered ASP code has been written to {output_file}")

def prompt_model(
    project_id: str,
    model_name: str,
    temperature: float,
    max_decode_steps: int,
    top_p: float,
    top_k: int,
    content: str,
    location: str = "us-central1",
    tuned_model_name: str = "",) :
    
    """Predict using a Large Language Model."""
    vertexai.init(project=project_id, location=location)
    model = TextGenerationModel.from_pretrained(model_name)
    
    if tuned_model_name:
        model = model.get_tuned_model(tuned_model_name)
    response = model.predict(
        content,
        temperature=temperature,
        max_output_tokens=max_decode_steps,
        top_k=top_k,
        top_p=top_p,)
    
    return(response.text)

def generating_asp_from_argument(argument):
    prompt = add_argument("Prompt to generate ASP code.txt", argument)

    response_text = prompt_model(
        project_id="aerial-grid-415517",
        model_name="text-bison-32k",
        temperature=0.2,
        max_decode_steps=8100,
        top_p=0.8,
        top_k=40,
        content=prompt,
        location="us-central1"
    )

    # Assuming the filter function modifies "filter.txt" directly,
    # first write the response to this file.
    with open("unfiltered asp code.txt", "w") as filt:
        filt.write(response_text)
    
    # Append the filtered content to "PaLM output.txt"
    # This avoids directly writing unfiltered response text and then filtered content,
    # streamlining the process to only include the desired output.
    with open("unfiltered asp code.txt", "r") as filt, open("ASP output.txt", 'a') as p:
        filtered_content = filt.read()
        p.write(filtered_content + "\n")
        print("ASP code generated")
    
    # Apply the filter to clean up "filter.txt"
apply_filter_to_asp_code("ASP output.txt","filtered asp code.txt")

def run_with_multiple_arguments(arguments_file):
    with open(arguments_file, 'r') as arguments:
        for argument in arguments:
            generating_asp_from_argument(argument)

def empty_file(file):
    with open(file, 'w'):
        pass

def clingo_compiling_check(file):
    # Clingo program
    program = clingo.Control()
    # Reading ASP code
    with open(file, 'r') as f:
        asp_code = f.read()
    # Load ASP code
    program.add('base', [], asp_code)
    # Compiling and solving
    try:
        program.ground([("base", [])])
        program.solve()
        return True
    except Exception as e:
        # Returns False if the ASP code has a wrong syntax and is not compiling
        return False
    
def solve_asp(file_path):
    # Read the ASP code from the file
    with open(file_path, 'r', encoding='utf-8') as file:
        asp_code = file.read()

    # Create a new clingo Control object
    solver = clingo.Control()
    
    # Add the ASP code to the solver
    solver.add("base", [], asp_code)
    
    # Ground the program
    solver.ground([("base", [])])

    # Open the file where the solutions will be saved
    empty_file("clingo_output.txt")
    with open("clingo_output.txt", 'w') as solution_file:
        
        # Define the on_model function to write models to the file
        def on_model(model):
            solution_file.write(f"Solution: {model}\n")
        
        # Solve the ASP program, calling on_model for each solution
        result = solver.solve(on_model=on_model)
        
        # Check if a solution exists and write the outcome to the file
        if result.satisfiable:
            print("A solution exists. Check 'clingo_output.txt' for details.")
        else:
            solution_file.write("No solution exists.\n")
            print("No solution exists. Check 'clingo_output.txt' for details.")

def generate_suggestions(asp_file):
    input_before = ""
    while_loop = True
    while while_loop:
        user_input = input("Please provide your input: ")
        if user_input.upper() == "STOP":
            print("STOPPED")
            break
        
        # Reading the prompt template for generating keywords
        with open('Prompt for Keywords.txt', 'r') as file:
            prompt = file.read().replace("$$$$$$$$$$$$$$$$$$$$", user_input)
        
        # Generate keywords using the prompt_model function
        response_text = prompt_model(
            project_id="aerial-grid-415517",
            model_name="text-bison-32k",
            temperature=0.2,
            max_decode_steps=8100,
            top_p=0.8,
            top_k=40,
            content=prompt,
            location="europe-west1"
        )
        
        # Extracting keywords from the generated text
        # print("Keywords Identified")
        keywords = response_text.split('\n, ')
        # print(keywords)

        empty_file("clingo_output.txt")
        for keyword in keywords:
            print(keyword)
            with open(asp_file, "r") as aspf:
                aspf_content = aspf.read()
                # Assuming 'encoding' contains your ASP encoding with placeholders for keywords
                if "(" + keyword in aspf_content or " " + keyword in aspf_content:
                    asp_code = aspf_content  # + encoding.replace("§§§", keyword)
                    # Assuming get_clingo_output processes and writes to "clingo_output.txt"
                    solve_asp(asp_code)
                    # print("KEYWORD FINISHED")

        # Reading the updated "clingo_output.txt" for the next prompt
        with open("clingo_output.txt", "r") as cof:
            clingo_output = cof.read()

        # Preparing the prompt with clingo output and user input for the next suggestion
        with open("Prompt for Autocompleting with clingo.txt", "r") as acwt:
            prompt = acwt.read()
            prompt_with_clingo = prompt.replace("????????????????????", clingo_output)
            prompt_with_clingo_and_text = prompt_with_clingo.replace("!!!!!!!!!!!!!!!!!!!!", user_input)

            # Generate suggestions using the updated prompt
        response_text = prompt_model(
            project_id="aerial-grid-415517",
            model_name="text-bison-32k",
            temperature=0.2,
            max_decode_steps=8100,
            top_p=0.8,
            top_k=40,
            content=prompt_with_clingo_and_text,
            location="europe-west1"
        )
        
        if "Positive:" in response_text:
            print("\nPositive Aspects")
            start_pos = response_text.find("Positive:") + len("Positive:")
            end_pos = response_text.find("Negative:") if "Negative:" in response_text else len(response_text)
            positive_aspects = response_text[start_pos:end_pos].strip()
    
    # Assuming aspects are listed in lines
        for aspect in positive_aspects.split('\n'):
            if aspect.strip():  # Ensure the line is not empty
                print(f" {aspect.strip()}")

        if "Negative:" in response_text:
                print("\nNegative Aspects")
                start_pos = response_text.find("Negative:") + len("Negative:")
                negative_aspects = response_text[start_pos:].strip()
    # Assuming aspects are listed in lines
        for aspect in negative_aspects.split('\n'):
            if aspect.strip():  # Ensure the line is not empty
                print(f" {aspect.strip()}")
        
    input_before = input_before + (user_input + " ")

def main():
    # empty_file("ASP output.txt")
    
    # # type the argument dataset name you want to use here!
    # run_with_multiple_arguments("4arguments.txt")
    
    generate_suggestions("filtered_cmv_asp_code.txt")
    # type "stop" to discontinue

if __name__ == "__main__":
    main()
