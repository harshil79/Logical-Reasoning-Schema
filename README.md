# File Description for the Schema
1. The two argument database .txt files `10000arguments_argsme.txt and 10000arguments_cmv.txt`
2. A prompt for generating ASP code directly from the argument dataset `Prompt to Generate ASP code.txt`
3. The two ASP code .txt files based on the argument database `10000arguments_argsme_asp.txt and 10000arguments_cmv_asp.txt`
4. The two filtered/refined ASP code .txt files `filtered_argsme_asp_code.txt and filtered_cmv_asp_code.txt`
5. A prompt file for deducing keywords from the sentence prompt by the user to the LLM `Prompt for Keywords.txt`
6. A prompt file for generating suggestions from clingo output `Prompt for Autocompleting with clingo.txt`

# Working
## With users own dataset

1. Code accepts user dataset `run with multiple arguments`.
2. Converts the dataset into an ASP code using a prompt `Prompt to generate ASP code.txt`.

> An ASP code needs to be compiled via clingo compilor in order to generate all possible relations.
> This clingo output will be used to generate suggestions.
> For compiling the ASP code filtering has to be carried out.
> This filtering will remove all unwanted characters, words, sentences which are not a part of ASP code.
> Example: Special Characters ('`*<>~%$‘’"é£á^&#ē|@ü+/), not allowed words(not,asp), numerics(1,2,3), incomplete sentences.

3. Filter the ASP code into a compilable format and store it into a new file with filtered asp code.
4. User prompts with an incomplete sentence.
5. Code generates keywords from the sentence using a prompt `Prompt for Keywords.txt`
6. Code searches the generated Keywords from the filtered ASP code file.
7. The matched ASP code lines are compiled using clingo compilor. `Compiling Check`

> Compiling check is just a step which ensures the ASP code is in perfect format.

8. After successfull compilation a clingo output is generated based on the compiled ASP code. `ASP solver` & `clingo_output.txt`.
9. The Suggestions are generated using the clingo output .txt file using a prompt `Prompt for Autocompleting with Clingo.txt`

## With predifined dataset 
`10000arguments_argsme.txt and 10000arguments_cmv.txt`

**Basically the dataset is fixed** 
**A filtered ASP code file is already generated and is used as a dataset for generating suggestions.**

1. User prompts with an incomplete sentence.
2. Code generates keywords from the sentence using a prompt `Prompt for Keywords.txt`
3. Code searches the generated Keywords from the filtered ASP code file. `filtered_argsme_asp_code.txt and filtered_cmv_asp_code.txt`
4. The matched ASP code lines are compiled using clingo compilor. `Compiling Check`

> Compiling check is just a step which ensures the ASP code is in perfect format.
 
5. After successfull compilation a clingo output is generated based on the compiled ASP code. `ASP solver` & `clingo_output.txt`.
6. The Suggestions are generated using the clingo output .txt file using a prompt `Prompt for Autocompleting with Clingo.txt`
