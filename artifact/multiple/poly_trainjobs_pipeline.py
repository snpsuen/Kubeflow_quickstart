import kfp
from kfp import dsl

@dsl.component(base_image='snpsuen/python-3.10-kubectl:v01')
def launch_load_data_trainjob():
    import subprocess
    subprocess.run([
        "kubectl", "apply", "-f",
        "https://raw.githubusercontent.com/snpsuen/Kubeflow_quickstart/refs/heads/main/artifact/multiple/load_data_job.yaml"
    ], check=True)
    print("Load data trainjob has been submitted.")

@dsl.component(base_image='snpsuen/python-3.10-kubectl:v01')
def launch_prepare_data_trainjob():
    import subprocess
    subprocess.run([
        "kubectl", "apply", "-f",
        "https://raw.githubusercontent.com/snpsuen/Kubeflow_quickstart/refs/heads/main/artifact/multiple/prepare_data_job.yaml"
    ], check=True)
    print("Prepare data trainjob has been submitted.")

@dsl.component(base_image='snpsuen/python-3.10-kubectl:v01')
def launch_train_model_trainjob():
    import subprocess
    subprocess.run([
        "kubectl", "apply", "-f",
        "https://raw.githubusercontent.com/snpsuen/Kubeflow_quickstart/refs/heads/main/artifact/multiple/train_model_job.yaml"
    ], check=True)
    print("Train model trainjob has been submitted.")

@dsl.component(base_image='snpsuen/python-3.10-kubectl:v01')
def launch_model_forecast_trainjob():
    import subprocess
    subprocess.run([
        "kubectl", "apply", "-f",
        "https://raw.githubusercontent.com/snpsuen/Kubeflow_quickstart/refs/heads/main/artifact/multiple/model_forecast_job.yaml"
    ], check=True)
    print("Model forecast trainjob has been submitted.")

@dsl.pipeline(
    name="Multiple Trainjobs Pipeline",
    description="A pipeline to launch multiple train jobs using components"
)
def poly_trainjobs_pipeline():
  launch_load_data_trainjob()
  launch_prepare_data_trainjob()
  launch_train_model_trainjob()
  launch_model_forecast_trainjob()
  
if __name__ == "__main__":
    from kfp import compiler
    compiler.Compiler().compile(simple_trainjob_pipeline, "poly_trainjobs_pipeline.yaml")
