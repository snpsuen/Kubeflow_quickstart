## GPT Training Pipeline

A Kubeflow pipeline is implemented to train up a toy GPT model and use it to generate text in response to user prompts. It consists of these task components in order
1. Load corpus data
2. Create and train up a GPT model
3. Run an interactive prompt session to generate text

### TL; DR

![GPT_Trainjobs_Pipeline](gpt_trainjobs_pipeline_20250820.png)

### Setup Overview

The steps and artifacts taken to build and run the build the pipelines are similar those involved in our earlier example of a pipeline of multiple train jobs (see [here](../multiple/readme.md)). The GPT model in use is created with all the standard LLM functions or capabilities, duch You may customise the python scripts by changing the input data, model hyperparemeters and ohers
