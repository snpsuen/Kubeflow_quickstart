import kfp
from kfp import dsl

@dsl.component(base_image='snpsuen/python-3.10-kubectl:v01')
def launch_load_data_trainjob():
    import subprocess
    import time
    subprocess.run([
        "kubectl", "apply", "-f",
        "https://raw.githubusercontent.com/snpsuen/Kubeflow_quickstart/refs/heads/main/artifact/multiple/load_data_job.yaml"
    ], check=True)
    command = "kubectl -n training get trainjob load-data-job -o=jsonpath='{.status.conditions[*].type}'"
    while (subprocess.check_output(command, shell=True, text=True) != "Complete"):
        time.sleep(1)

@dsl.component(base_image='snpsuen/python-3.10-kubectl:v01')
def launch_prepare_data_trainjob():
    import subprocess
    subprocess.run([
        "kubectl", "apply", "-f",
        "https://raw.githubusercontent.com/snpsuen/Kubeflow_quickstart/refs/heads/main/artifact/multiple/prepare_data_job.yaml"
    ], check=True)
    command = "kubectl -n training get trainjob prepare-data-job -o=jsonpath='{.status.conditions[*].type}'"
    while (subprocess.check_output(command, shell=True, text=True) != "Complete"):
        time.sleep(1)

@dsl.component(base_image='snpsuen/python-3.10-kubectl:v01')
def launch_train_model_trainjob():
    import subprocess
    subprocess.run([
        "kubectl", "apply", "-f",
        "https://raw.githubusercontent.com/snpsuen/Kubeflow_quickstart/refs/heads/main/artifact/multiple/train_model_job.yaml"
    ], check=True)
    command = "kubectl -n training get trainjob train-model-job -o=jsonpath='{.status.conditions[*].type}'"
    while (subprocess.check_output(command, shell=True, text=True) != "Complete"):
        time.sleep(1)

@dsl.component(base_image='snpsuen/python-3.10-kubectl:v01')
def launch_model_forecast_trainjob():
    import subprocess
    subprocess.run([
        "kubectl", "apply", "-f",
        "https://raw.githubusercontent.com/snpsuen/Kubeflow_quickstart/refs/heads/main/artifact/multiple/model_forecast_job.yaml"
    ], check=True)
    command = "kubectl -n training get trainjob model-forecast-job -o=jsonpath='{.status.conditions[*].type}'"
    while (subprocess.check_output(command, shell=True, text=True) != "Complete"):
        time.sleep(1)

@dsl.pipeline(
    name="Multiple Trainjobs Pipeline",
    description="A pipeline to launch multiple train jobs using components"
)
def poly_trainjobs_pipeline():
    load_data_task = launch_load_data_trainjob()
    prepare_data_task = launch_prepare_data_trainjob()
    train_model_task = launch_train_model_trainjob()
    model_forecast_task = launch_model_forecast_trainjob()
    prepare_data_task.after(load_data_task)
    train_model_task.after(prepare_data_task)
    model_forecast_task.after(train_model_task)

if __name__ == "__main__":
    from kfp import compiler
    compiler.Compiler().compile(poly_trainjobs_pipeline, "poly_trainjobs_pipeline.yaml")
