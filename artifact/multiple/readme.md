## Pipline for multiple train jobs

A more realistic approach is to break down a monolithic pipeline into a workflow of multiple train jobs that are to be carried out in this order.
1. Load raw data
2. Slice and dice data sets to prepare for training
3. Train a DL model
4. Use the model to make a forescast

### TL; DR

![Kubeflow_shoestring](kubeflow_shoestring.png)
