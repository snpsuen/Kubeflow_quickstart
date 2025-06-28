import kfp
from kfp import dsl

@dsl.component(base_image='snpsuen/python-3.10-kubectl:v01')
def launch_simple_trainjob():
    import subprocess
    subprocess.run([
        "kubectl", "apply", "-f",
        "https://raw.githubusercontent.com/snpsuen/Deep_Learning_Data/refs/heads/main/script/pytorch-simple-trainer.yaml"
    ], check=True)
    print("Simple trainjob has been submitted.")

@dsl.pipeline(
    name="Simple Trainjob Pipeline",
    description="Simple pipeline to launch a trainjob using a component"
)
def simple_trainjob_pipeline():
    launch_simple_trainjob()

if __name__ == "__main__":
    from kfp import compiler
    compiler.Compiler().compile(simple_trainjob_pipeline, "simple_trainjob_pipeline.yaml")
