## Pipline for multiple train jobs

A more realistic approach is to break down a monolithic pipeline into a workflow of multiple train jobs. To start with, let's consider a ML life cycle that is typically driven by the following pipeline components in order.
1. Load raw data
2. Slice and dice data sets to prepare for training
3. Train up a DL model
4. Use the model to forecast

Hope the exercise can serve as a template for building other pipelines that involve similar train jobs. 

### TL; DR

![Multiple_pipeline_coomponents](multiple_pipeline_components.png)

### Package the Pytorch scripts in a docker image.





