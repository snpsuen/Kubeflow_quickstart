import kfp
from kfp import dsl

@dsl.component(base_image='snpsuen/python-3.10-kubectl:v01')
def launch_load_corpus_trainjob():
    import subprocess
    import time
    subprocess.run([
        "kubectl", "apply", "-f",
        "https://raw.githubusercontent.com/snpsuen/Kubeflow_quickstart/refs/heads/main/artifact/gpt/load_corpus_job.yaml"
    ], check=True)
    command = "kubectl -n training get trainjob load-corpus-job -o=jsonpath='{.status.conditions[*].type}'"
    while (subprocess.check_output(command, shell=True, text=True) != "Complete"):
        time.sleep(1)

@dsl.component(base_image='snpsuen/python-3.10-kubectl:v01')
def launch_train_gpt_trainjob():
    import subprocess
    import time
    subprocess.run([
        "kubectl", "apply", "-f",
        "https://raw.githubusercontent.com/snpsuen/Kubeflow_quickstart/refs/heads/main/artifact/gpt/train_gpt_job.yaml"
    ], check=True)
    command = "kubectl -n training get trainjob train-gpt-job -o=jsonpath='{.status.conditions[*].type}'"
    while (subprocess.check_output(command, shell=True, text=True) != "Complete"):
        time.sleep(1)

@dsl.component(base_image='snpsuen/python-3.10-kubectl:v01')
def launch_generative_prompt_trainjob():
    import subprocess
    import time
    subprocess.run([
        "kubectl", "apply", "-f",
        "https://raw.githubusercontent.com/snpsuen/Kubeflow_quickstart/refs/heads/main/artifact/gpt/generative_prompt_job.yaml"
    ], check=True)
    command = "kubectl -n training get trainjob generative-prompt-job -o=jsonpath='{.status.conditions[*].type}'"
    while (subprocess.check_output(command, shell=True, text=True) != "Complete"):
        time.sleep(1)

@dsl.pipeline(
    name="GPT Trainjobs Pipeline",
    description="A pipeline to launch gpt train jobs using components"
)
def gpt_trainjobs_pipeline():
    load_corpus_task = launch_load_corpus_trainjob()
    train_gpt_task = launch_train_gpt_trainjob()
    generative_prompt_task = launch_generative_prompt_trainjob()
    train_gpt_task.after(load_corpus_task)
    generative_prompt_task.after(train_gpt_task)

if __name__ == "__main__":
    from kfp import compiler
    compiler.Compiler().compile(gpt_trainjobs_pipeline, "gpt_trainjobs_pipeline.yaml")
