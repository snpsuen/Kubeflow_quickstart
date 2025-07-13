## Pipeline for running multiple train jobs

A more realistic approach is to break down a monolithic pipeline into a workflow of multiple train jobs. To start with, let's consider a ML life cycle that is typically driven by the following pipeline components in order.
1. Load raw data
2. Slice and dice data sets to prepare for training
3. Train up a DL model
4. Use the model to forecast

Hope the exercise can serve as a template for building other pipelines that involve similar train jobs. 

### TL; DR

![Multiple_pipeline_coomponents](multiple_pipeline_components.png)

### Containerize your subject-specific DL source code

Place the pytorch scripts in a suitable environment as per the directory layout below.
```
workspace/
├── simple_train_lib.py
├── call_train_lib.py
├── call_load_data.py
├── call_prepare_data.py
├── call_train_model.py
└── call_model_forecast.py
```

Package the scripts into a docker image, which will be used to spin up the train job worker pods. The entry point command specified here is only a filler and will certainly be overrided when a pod is created from the image to perform a specific train job. In this example, the image is tagged snpsuen/call_train_lib:02.
```
cat > Dockerfile <<EOF
FROM python:3.13.5-slim-bookworm
RUN pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu && pip install pandas matplotlib
RUN apt-get update && apt-get install -y nano procps
WORKDIR /workspace
COPY . .
CMD [ "python", "./call_train_lib.py"]
EOF

docker build -t snpsuen/call_train_lib:02 .
```

### Define Trainjob and Trainingruntime CRDs

Refer to the following manifests in this repo directory for the TrainJob and TrainingRuntime CRDs defined to serve the corresponding train jobs in the pipeline.
1. [load_data_job.yaml](load_data_job.yaml)
2. [prepare_data_job.yaml](prepare_data_job.yaml)
3. [train_model_job.yaml](train_model_job.yaml)
4. [model_forecast.yaml](model_forecast.yaml)

All train jobs are eventually implemented by job pods that share the same docker image but start with different entry point commands.
<table>
	<tr>
		<th scope="col" align="left">Manifest</th>
		<th scope="col" align="left">TrainJob CRD</th>
		<th scope="col" align="left">TrainingRuntime CRD</th>
		<th scope="col" align="left">Job Pod</th>
		<th scope="col" align="left">Docker Image</th>
		<th scope="col" align="left">Entry Point Command</th>
	</tr>
	<tr>
		<td align="left">load_data_job.yaml</td>
		<td align="left">load-data-job</td>
		<td align="left">load-data-runtime</td>
		<td align="left">load-data-pod</td>
		<td align="left">snpsuen/call_train_lib:02</td>
		<td align="left">python ./call_load_data.py</td>			
	</tr>
	<tr>
		<td align="left">prepare_data_job.yaml</td>
		<td align="left">prepare-data-job</td>
		<td align="left">prepare-data-runtime</td>
		<td align="left">prepare-data-pod</td>
		<td align="left">snpsuen/call_train_lib:02</td>
		<td align="left">python ./call_prepare_data.py</td>
	</tr>
	<tr>
		<td align="left">train_model_job.yaml</td>
		<td align="left">train-model-job</td>
		<td align="left">train-model-runtime</td>
		<td align="left">train-model-pod</td>
		<td align="left">snpsuen/call_train_lib:02</td>
		<td align="left">python ./call_train_model.py</td>
	</tr>
	<tr>
		<td align="left">model_forecast_job.yaml</td>
		<td align="left">model-forecast-job</td>
		<td align="left">model-forecast-runtime</td>
		<td align="left">model-forecast-pod</td>
		<td align="left">snpsuen/call_train_lib:02</td>
		<td align="left">python ./call_model_forecast.py</td>
	</tr>
</table>

To facilitate passage of data from one job pod to another, pytorch objects returned by a pod, mostly in the form of various data sets or models, are written to a file system via torch.save(). They are subsequently fed into the receving pod using torch.load().

We go for a quick and dirty option whereby a designated hostpath volume, /var/tmp/pytorch, is shared by the job pods via the container mount point /pytorch. To ensure all the pods will access the same copy of the hostpath volume throughout the pipeline, we schedule them explicitly to run on the same Kubernetes node by hardcoding the nodename field of the pod template, namely template.spec.nodename. 

This rather ugly approach can be refined by using an NFS volume to share data between the job pods. We will leave it to later discussion.

### Set up a Kubeflow pipeline

We proceed to set up a Kubeflow pipeline based on the KFP script, [poly_trainjobs_pipeline.py](poly_trainjobs_pipeline.py). As expected, there are four pipeline components in total and each will run as a pod from the same docker image where kubectl is invoked to create the designated TrainJob and TrainingRuntime CRDs.

<table>
	<tr>
		<th scope="col" align="left">Pipeline Component</th>
		<th scope="col" align="left">Docker Image</th>
		<th scope="col" align="left">kubectl Command</th>
	</tr>
	<tr>
		<td align="left">launch_load_data_trainjob</td>
		<td align="left">snpsuen/python-3.10-kubectl:v01</td>
		<td align="left">kubectl apply -f load_data_job.yaml</td>			
	</tr>
	<tr>
		<td align="left">launch_prepare_data_trainjob</td>
		<td align="left">snpsuen/python-3.10-kubectl:v01</td>
		<td align="left">kubectl apply -f prepare_data_job.yaml</td>
	</tr>
	<tr>
		<td align="left">launch_train_model_trainjob</td>
		<td align="left">snpsuen/python-3.10-kubectl:v01</td>
		<td align="left">kubectl apply -f train_model_job.yaml</td>
	</tr>
	<tr>
		<td align="left">launch_model_forecast_trainjob</td>
		<td align="left">snpsuen/python-3.10-kubectl:v01</td>
		<td align="left">kubectl apply -f _model_forecast_job.yaml</td>
	</tr>
</table>

An important consideration is to establish dependency between the pipeline components so that they will be executed in the desirable order. This is evident from the definition of the pipeline function in the KFP script.
```
def poly_trainjobs_pipeline():
    load_data_task = launch_load_data_trainjob()
    prepare_data_task = launch_prepare_data_trainjob()
    train_model_task = launch_train_model_trainjob()
    model_forecast_task = launch_model_forecast_trainjob()

    prepare_data_task.after(load_data_task)
    train_model_task.after(prepare_data_task)
    model_forecast_task.after(train_model_task)
```

In this way, a pipeline component is ready to pass the floor to the following component only after the TrainJob CRD it created is observed to have reached the Complete status. For example, the pipeline will wait for load-data-job to complete before progressing to prepare_data_task.
```
command = "kubectl -n training get trainjob load-data-job -o=jsonpath='{.status.conditions[*].type}'"
while (subprocess.check_output(command, shell=True, text=True) != "Complete"):
	time.sleep(1)
```
Finally, run python on the script to compile it into a yaml file, [poly_trainjobs_pipeline.yaml](poly_trainjobs_pipeline.yaml).

Now we can move on to the next step of running the pipeline on Kubeflow Pipelines.

### Try it out on Kubeflow Pipelines

Upload the pipeline yaml, [poly_trainjobs_pipeline.yaml](poly_trainjobs_pipeline.yaml), via the UI to Kubeflow Pipelines.

![pipeline_20250711_01_screen01](pipeline_20250711_01_screen01.PNG)
![pipeline_20250711_01_screen02](pipeline_20250711_01_screen02.PNG)

Start a run of the pipeline.

![pipeline_20250711_01_screen03](pipeline_20250711_01_screen03.PNG)
![pipeline_20250711_01_screen05](pipeline_20250711_01_screen05.PNG)

Observe the pipeline completes after 6 mins.

![pipeline_20250711_02_screen01](pipeline_20250711_02_screen01.PNG)
![pipeline_20250711_02_screen02](pipeline_20250711_02_screen02.PNG)
![pipeline_20250711_02_screen03](pipeline_20250711_02_screen03.PNG)

The train jobs are launched by the following pipeline running pods on the data plane of Kubeflow Pipelines.
```
keyuser@ubunclone:~$ kubectl -n kubeflow get pods
...
multiple-trainjobs-pipeline-fzfjb-system-container-driver-1654498691   0/2     Completed   0             87m
multiple-trainjobs-pipeline-fzfjb-system-container-driver-2201144676   0/2     Completed   0             85m
multiple-trainjobs-pipeline-fzfjb-system-container-driver-3114394      0/2     Completed   0             89m
multiple-trainjobs-pipeline-fzfjb-system-container-driver-4215877059   0/2     Completed   0             88m
multiple-trainjobs-pipeline-fzfjb-system-container-impl-1019964485     0/2     Completed   0             86m
multiple-trainjobs-pipeline-fzfjb-system-container-impl-2087507732     0/2     Completed   0             89m
multiple-trainjobs-pipeline-fzfjb-system-container-impl-2098615850     0/2     Completed   0             84m
multiple-trainjobs-pipeline-fzfjb-system-container-impl-2659625605     0/2     Completed   0             87m
multiple-trainjobs-pipeline-fzfjb-system-dag-driver-1389824855         0/2     Completed   0             89m
...
```

Here are the TrainJob CRDs created by the pipeline.
```
keyuser@ubunclone:~$ kubectl -n training get trainjob
NAME                 STATE      AGE
load-data-job        Complete   3h24m
model-forecast-job   Complete   3h20m
prepare-data-job     Complete   3h23m
train-model-job      Complete   3h22m
```

The train jobs are served by the following worker pods that do the actual work of running the subject-specific DL scripts.
```
keyuser@ubunclone:~$ kubectl -n training get pods
NAME                                             READY   STATUS      RESTARTS   AGE
load-data-job-load-data-rj-0-0-lh974             0/1     Completed   0          3h12m
model-forecast-job-model-forecast-rj-0-0-rqxrf   0/1     Completed   0          3h7m
prepare-data-job-prepare-data-rj-0-0-h2zjs       0/1     Completed   0          3h10m
train-model-job-train-model-rj-0-0-dbrpk         0/1     Completed   0          3h9m
```

Finally, check out the pod logs for the expected results from the scripts.
```
keyuser@ubunclone:~$ kubectl -n training logs load-data-job-load-data-rj-0-0-lh974
(1) Reading CSV source ...

Type of df =  <class 'pandas.core.frame.DataFrame'>
df.shape =  (144, 2)
Type of timeseries =  <class 'numpy.ndarray'>
timeseries.shape =  (144, 1)
Type of train =  <class 'numpy.ndarray'>
train.shape =  (100, 1)
Type of test =  <class 'numpy.ndarray'>
test.shape =  (44, 1)
Type of forecast =  <class 'numpy.ndarray'>
forecast.shape =  (4, 1)
Saving train data to /pytorch/train.pt ...
Saving test data to /pytorch/test.pt ...
Saving forecast data to /pytorch/forecast.pt ...
keyuser@ubunclone:~$

keyuser@ubunclone:~$ kubectl -n training logs prepare-data-job-prepare-data-rj-0-0-h2zjs
loading train data from /pytorch/train.pt ...
loading test data from /pytorch/test.pt ...
loading forecast data from /pytorch/forecast.pt ...
(2) Preparing training data ...

Type of X_train, type of y_train =  <class 'torch.Tensor'> <class 'torch.Tensor'>
X_train.shape(samples, timesteps, features), y_train.shape(samples, features) =  torch.Size([96, 4, 1]) torch.Size([96, 1])
Type of X_test, type of y_test =  <class 'torch.Tensor'> <class 'torch.Tensor'>
X_test.shape(samples, timesteps, features), y_test.shape(samples, features) =  torch.Size([40, 4, 1]) torch.Size([40, 1])
Type of X_forecast =  <class 'torch.Tensor'>
X_forecast.shape(samples, timesteps, features) =  torch.Size([1, 4, 1])
Saving X_train data to /pytorch/X_train.pt ...
Saving y_train data to /pytorch/y_train.pt ...
Saving X_test data to /pytorch/X_test.pt ...
Saving y_test data to /pytorch/y_test.pt ...
Saving X_forecast data to /pytorch/X_forecast.pt ...
keyuser@ubunclone:~$

keyuser@ubunclone:~$ kubectl -n training logs train-model-job-train-model-rj-0-0-dbrpk
(3) Creating training model ...

loading X_train data from /pytorch/X_train.pt ...
loading y_train data from /pytorch/y_train.pt ...
loading X_test data from /pytorch/X_test.pt ...
loading y_test data from /pytorch/y_test.pt ...
(4) Training and evaluating the model ...

Epoch 0: train RMSE 233.6494, test RMSE 427.5275
Epoch 10: train RMSE 225.7769, test RMSE 419.3704
Epoch 20: train RMSE 218.8507, test RMSE 412.1515
Epoch 30: train RMSE 213.2877, test RMSE 406.3551
Epoch 40: train RMSE 208.0894, test RMSE 400.9236
Epoch 50: train RMSE 203.0791, test RMSE 395.6733
Epoch 60: train RMSE 198.2084, test RMSE 390.5540
Epoch 70: train RMSE 193.4573, test RMSE 385.5443
Epoch 80: train RMSE 188.7998, test RMSE 380.6164
Epoch 90: train RMSE 184.2362, test RMSE 375.7700
Saving trained model weight data to /pytorch/trained_weights.pt ...
keyuser@ubunclone:~$

keyuser@ubunclone:~$ kubectl -n training logs model-forecast-job-model-forecast-rj-0-0-rqxrf
(3) Creating training model ...

Loading trained model weight data from /pytorch/trained_weights.pt ...
Loading X_forecast data from /pytorch/X_forecast.pt ...
(5) Forecasting from the model ...

Forecast input =  tensor([[[508.],
         [461.],
         [390.],
         [432.]]])
Forecast output =  tensor([[57.4423]])
Saving y_forecast data to /pytorch/y_forecast.pt ...
keyuser@ubunclone:~$
```
