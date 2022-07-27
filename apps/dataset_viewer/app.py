from distutils.command.build import build
import streamlit as st
import pandas as pd
import numpy as np
import glob
import importlib
import datasets
from datasets import load_dataset
from dataloader import Collection

def render_features(features):
    """Recursively render the dataset schema (i.e. the fields)."""
    if isinstance(features, dict):
        return {k: render_features(v) for k, v in features.items()}
    if isinstance(features, datasets.features.ClassLabel):
        return features.names

    if isinstance(features, datasets.features.Value):
        return features.dtype

    if isinstance(features, datasets.features.Sequence):
        return {"[]": render_features(features.feature)}
    return features

def list_datasets():
    """Get all the datasets to work with."""
    dataset_list = Collection()._find_datasets()
    dataset_list.sort(key=lambda x: x[0].lower())
    return dataset_list

def get_dataset(dataset_path: str, subset_name=None):
    return datasets.load_dataset(str(dataset_path), subset_name)

def get_dataset_confs(dataset_path: str):
    "Get the list of confs for a dataset."
    module_path = datasets.load.dataset_module_factory(str(dataset_path)).module_path
    # Get dataset builder class from the processing script
    builder_cls = datasets.load.import_main_class(module_path, dataset=True)
    # Instantiate the dataset builder
    confs = builder_cls.BUILDER_CONFIGS
    if confs and len(confs) > 1:
        return confs, builder_cls.DEFAULT_CONFIG_NAME
    return [], None


get_dataset = st.cache(get_dataset)
list_datasets = st.cache(list_datasets)
get_dataset_confs = st.cache(get_dataset_confs)

def load_ds(dataset):
    dataset_name, dataset_path = dataset
    configs, default = get_dataset_confs(dataset_path)

    conf_option = None
    if len(configs) > 0:
        conf_option = st.sidebar.selectbox(
            "Subset", 
            configs, 
            index=[x.name for x in configs].index(default), 
            format_func=lambda a: a.name
        )
    subset_name = str(conf_option.name) if conf_option else None

    dataset = get_dataset(dataset_path, subset_name)

    splits = list(dataset.keys())
    index = 0
    if "train" in splits:
        index = splits.index("train")
    split = st.sidebar.selectbox("Split", splits, key="split_select", index=index)
    dataset = dataset[split]

    step = 50
    example_index = st.sidebar.number_input(
        f"Select the example index (Size = {len(dataset)})",
        min_value=0,
        max_value=len(dataset) - step,
        value=0,
        step=step,
        key="example_index_number_input",
        help="Offset = 50.",
    )

    st.sidebar.subheader("Dataset Schema")
    rendered_features = render_features(dataset.features)
    st.sidebar.write(rendered_features)

    st.header("Dataset: " + dataset_name + " " + (("/ " + conf_option.name) if conf_option else ""))

    

    source_link = "https://github.com/huggingface/datasets/blob/master/datasets/%s/%s.py" % (
        dataset_name,
        dataset_name,
    )
    st.markdown("*Homepage*: " + dataset.info.homepage + "\n\n*Dataset*: " + source_link)

    md = """
    %s
    """ % (
        dataset.info.description.replace("\\", "") if dataset_name else ""
    )
    st.markdown(md)

    # Display a couple (steps) examples
    for ex_idx in range(example_index, example_index + step):
        if ex_idx >= len(dataset):
            continue
        example = dataset[ex_idx]
        st.write(example)
        st.markdown("***")


def run_app():
    
    st.set_page_config(page_title="ThoughtSource⚡", layout="wide")

    # st.title('ThoughtSource⚡ Viewer')

    st.sidebar.markdown(
        "<center><a href='https://github.com/OpenBioLink/ThoughtSource'>💻Github - ThoughtSource⚡\n\n</a></center>",
        unsafe_allow_html=True,
    )

    st.sidebar.header('ThoughtSource⚡ Viewer')

    dataset = st.sidebar.selectbox(
        'Dataset',
        list_datasets(),
        format_func=lambda x: x[0]
    )

    load_ds(dataset)

if __name__ == "__main__":
    run_app()