## Kubeflow Quickstart

In this lab, we will walk you through the steps of uplifting a sample Pytorch deep learning notebook to Kubeflow on a shoestring, so to speak:
* Minimal Kubeflow ecosystem: Kubeflow Pipelines + Kubeflow Trainer V2
* Small footprint: Kind Kubernetes(1.32 or later) on a compute instance or VM, etc of 4GB memory and 20GB free disk space
* A working Pytorch notebook on Google Colab or Jupyter

The exercise may serve as a entry template for future extension to other Kubflow compoents like Katib, Model Registry or more complicated train jobs.

### TL; DR

![Kubeflow_shoestring](kubeflow_shoestring.png)

### Step by step walk through

1. Install Kubeflow Pipelines and Kubeflow Trainer V2
2. Download a chosen Pytorch notebook as a python script
3. Containerize the python script in a docker
4. Define the Kubeflow Trainer CRDs Trainjob and Trainingruntime
5. Prepare a docker image for the task of creating the Trainjob and Trainingruntime CRDs
6. Write a KFP script to define a Kubeflow pipleline job
7. Sort out RBAC beteen Kubeflow pipeline and Kubeflow Trainer
8. Upload the pipeline manifest and run the pipeline on the Kubeflow Pipeline UI

#### 1. Install Kubeflow Pipeline and Kubeflow Trainer V2 as standalone components

Install Kubeflow Piplines according to the [official guide](https://www.kubeflow.org/docs/components/pipelines/operator-guides/installation/).

```
export PIPELINE_VERSION=2.4.0
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref=$PIPELINE_VERSION"
kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/dev?ref=$PIPELINE_VERSION"
```

Heads up: When installing from the offical repo, the peristent volume claim (PVC) is set to 20GB each for the mino and mysql pods on the Kubeflow Pipelines control plane. As an alternative, version 2.4.0 of the offical repo is cloned into my github account with the PVC reduced to 10GB each for both pods. It is served at the master branch here. If necessary, you may opt to install the custom repo as follows.

```
kubectl apply -k "github.com/snpsuen/kubeflow-pipelines/manifests/kustomize/cluster-scoped-resources?ref=master"
kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
kubectl apply -k "github.com/snpsuen/kubeflow-pipelines/manifests/kustomize/env/platform-agnostic?ref=master"
```

Install Kubeflow Trainer according to the [official guide](https://www.kubeflow.org/docs/components/trainer/operator-guides/installation/).

```
kubectl apply --server-side -k "https://github.com/kubeflow/trainer.git/manifests/overlays/manager?ref=master"
kubectl apply --server-side -k "https://github.com/kubeflow/trainer.git/manifests/overlays/runtimes?ref=master"
```

#### 2. Download a chosen Pytorch notebook as a python script

Suppose you have chosen a working Pytorch notebook from Google Colab or Jupyter. Click *File->Download as* on the UI to download it as a python py script.

In this example, the lab uses a [simple Pytorch notebook](artifact/Pytorch_RNN_LSTM_AT_example05.ipynb) in the artiface directory of this repo. It is adapted from a Pytorch script written by Adrian Tam to train an LSTM DL model to predict about the number of airline passengers in a time series [(see here)](https://machinelearningmastery.com/lstm-for-time-series-prediction-in-pytorch/). The notebook sample has been downloaded as [pytorch_rnn_lstm_at_example05.py](artifact/pytorch_rnn_lstm_at_example05.py).

#### 3. Containerize the python script in a docker

Create a docker image based on python:3.13.5-slim-bookworm and install the packages pytorch, pandas and matplotlib. <br>
Specify *python ./pytorch_rnn_airpass_example05.py* as the default command to run when a container starts from the image.

In this example, the docker image is created and tagged as snpsuen/pytorch_rnn_airpass:05 under the default docker.io registry.

```
cat > Dockerfile <<EOF
FROM python:3.13.5-slim-bookworm
RUN pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu && pip install pandas matplotlib
RUN mkdir /workspace
WORKDIR /workspace
COPY ./pytorch_rnn_airpass_example05.py .
CMD [ "python", "./pytorch_rnn_airpass_example05.py"]
EOF

docker build -t snpsuen/pytorch_rnn_airpass:05 .
docker push snpsuen/pytorch_rnn_airpass:05
```

#### 4. Define the Kubeflow Trainer CRDs Trainjob and Trainingruntime

Create a namespace called training and define a Traingruntime CRD called pytorch-simple-runtime in that namespace for Kubeflow Trainer V2. <br>
In particular, pytorch-simple-runtime encompasses a replicated job that uses the docker image snpsuen/pytorch_rnn_airpass:05 created earlier in step 3.

```
kubectl create ns training
cat > pytorch-simple-trainer.yaml <<EOF
apiVersion: trainer.kubeflow.org/v1alpha1
kind: TrainingRuntime
metadata:
  name: pytorch-simple-runtime
  namespace: training # Or the namespace where your runtime will live
spec:
  template:
    metadata:
      name: pyrt-simple
      namespace: training
    spec:
      replicatedJobs:
        - name: pyrt-rj
          replicas: 1
          template:
            metadata:
              name: pyrt-rj-simple
              namespace: training
            spec:
              template:
                metadata: 
                  name: pyrt-simple-pod
                  namespace: training
                spec:
                  containers:
                    - command:
                        - "python"
                        - "/workspace/pytorch_rnn_airpass_example05.py"
                      image: snpsuen/pytorch_rnn_airpass:05
                      imagePullPolicy: Always
                      name: pyrt-simple-container
---
EOF
```

Similarly, define a TraingJob CRD called pytorch-simple-trainjob in training namespace for Kubeflow Trainer V2. <br>
More specifically, pytorch-simple-trainjob points to pytorch-simple-runtime in the .spec.runtimeRef fields.

```
cat >> pytorch-simple-trainer.yaml <<EOF
apiVersion: trainer.kubeflow.org/v1alpha1
kind: TrainJob
metadata:
  name: pytorch-simple-trainjob
  namespace: training # Or the namespace where your runtime will live
spec:
  runtimeRef:
    kind: TrainingRuntime
    name: pytorch-simple-runtime
EOF
```

You may find the two CRD manifests combined into a single yaml file [pytorch-simple-trainer.yaml](artifact/pytorch-simple-trainer.yaml) in the artiface directory.

#### 5. Prepare a docker image for creation of the Trainjob and Trainingruntime CRDs

To be continued ...


