import streamlit as st
from PIL import Image
from deepface import DeepFace
import numpy as np
import pandas as pd
import plotly.express as px
from typing import Dict
from typing import Tuple


def load_img(img: any) -> np.array:
    """
    This function loads the uploaded img obj and turn to np.array

    Returns:
        img_arr (np.array): img in numpy array
    """
    image_loaded = Image.open(img)
    image_arr = np.array(image_loaded.convert("RGB"))
    return image_arr


def show_img(sample: bool = False) -> Tuple:
    """
    This function displays the upload and loaded images.
    When the app first load, it will display sample family photos (Beckham family)
    After that, session_state['Init'] will set to false so that it can allow user to try their own.

    Args:
    sample (bool): If True, display the family pictures in sample

    Returns:
        img_father, img_mother, img_child: The files uploaded
    """
    # Display the uploaded images
    st.subheader("Upload pictures of your family to get started!")

    col1, col2, col3 = st.columns(3)
    if sample:
        img_father = "data/father.jpeg"
        img_child = "data/child.jpeg"
        img_mother = "data/mother.jpeg"
    else:
        img_father, img_child, img_mother = None, None, None

    with col1:
        if img_father is None:
            img_father = st.file_uploader(
                "Upload an image for father 👨", type=["png", "jpg", "jpeg"]
            )
        if img_father is not None:
            st.image(img_father, caption="Father", width=200)
    with col2:
        if img_child is None:
            img_child = st.file_uploader(
                "Upload an image for child 🧒👧", type=["png", "jpg", "jpeg"]
            )
        if img_child is not None:
            st.image(img_child, caption="Child", width=200)
    with col3:
        if img_mother is None:
            img_mother = st.file_uploader(
                "Upload an image for mother 👩", type=["png", "jpg", "jpeg"]
            )
        if img_mother is not None:
            st.image(img_mother, caption="Mother", width=200)

    return img_father, img_mother, img_child


def charts(paternal_result: Dict, maternal_result: Dict, distance_metrics: str):
    """
    This function create a bar chart based on the analysis result

    Args:
        paternal_result (Dict): father analysis result
        maternal_result (Dict): mother analysis result
        distance_metrics (str): name of the distance metrics used
    """

    data = {
        "parent": ["Father", "Mother"],
        "feature": ["face", "face"],
        "similarity": [
            -1 + paternal_result["distance"]
            if distance_metrics == "cosine"
            else 1.0 / (1 + paternal_result["distance"]),
            1 - maternal_result["distance"]
            if distance_metrics == "cosine"
            else 1.0 / (1 + maternal_result["distance"]),
        ],
    }
    chart_data = pd.DataFrame(data=data)
    fig = px.bar(
        chart_data,
        x="similarity",
        y="feature",
        color="parent",
        title="Similarity",
        orientation="h",
        height=250,
    )
    st.plotly_chart(fig, theme="streamlit")


def run_deepface(img1: any, img2: any, model_name: str, distance_metrics: str) -> Dict:
    """
    This function use deepface.verify to compare the img1 and img2 to get similarity

    Args:
        img1 (any): image 1
        img2 (any): image 2
        model_name (str): name of the deepL model for factial detection
        distance_metrics (str): name of the distance metrics

    Returns:
        result (Dict): result of the analysis
    """
    try:
        result = DeepFace.verify(
            img1_path=load_img(img1),
            img2_path=load_img(img2),
            model_name=model_name,
            detector_backend="mtcnn",
            distance_metric=distance_metrics,
        )
        return result
    except ValueError:
        st.error("Something wrong with either the pictures. Upload them again")
        return None


def compare_image(
    img_father: any,
    img_mother: any,
    img_child: any,
    distance_metrics: str = "cosine",
    model_name: str = "Facenet",
) -> Tuple:
    """
    This function run analysis to compare the parent-child images.
    After successful run of the comparisons, this function also plot a bar chart
    to display the result visually

    Args:
        img_father (any): streamlit file uploader obj for father
        img_mother (any): streamlit file uploader obj for mother
        img_child (any):  streamlit file uploader obj for child
        distance_metrics (str, optional): name of the distance metrics used for comparison. Defaults to "cosine".
        model_name (str, optional): name of the model used for facial detection. Defaults to "Facenet".

    Returns:
        paternal_result, maternal_result: analysis results
    """
    # Run the analysis
    with st.spinner("Analyzing the images..."):
        paternal_result = run_deepface(
            img_father, img_child, model_name, distance_metrics
        )
        maternal_result = run_deepface(
            img_mother, img_child, model_name, distance_metrics
        )

    # Show the results
    if paternal_result is not None and maternal_result is not None:
        charts(paternal_result, maternal_result, distance_metrics=distance_metrics)

        if maternal_result["distance"] < paternal_result["distance"]:
            st.success("The child looks more like mother.")
        else:
            st.success("The child looks more like father.")

        return maternal_result["distance"], paternal_result["distance"]


def add_click():
    st.session_state.clicks += 1


st.set_page_config(layout="wide", page_title="Family Facial Comparison")

st.header("Whom does your child look like? 👨‍👩‍👧‍👦")
if "clicks" not in st.session_state:
    st.session_state.clicks = 0

# Display settings in sidebar
with st.sidebar:
    distance_metrics = st.radio(
        "Distance Metrics", ["cosine", "euclidean", "euclidean_l2"], index=0
    )
    model = st.selectbox(
        "Image Models",
        [
            "Facenet",
            "VGG-Face",
            "Facenet512",
            "OpenFace",
            "DeepFace",
            "DeepID",
            "ArcFace",
            "Dlib",
            "SFace",
        ],
    )
    url = "https://github.com/serengil/deepface"
    st.markdown(f"This app uses [deepface library]({url}).")

click = st.button("Try it yourself.", on_click=add_click)

# Ask for the images. Run a sample in the begining
img_father, img_mother, img_child = show_img(sample=st.session_state["clicks"] == 0)

# Compare the images and display the result
if img_father is not None and img_mother is not None and img_child is not None:
    compare_image(
        img_father,
        img_mother,
        img_child,
        distance_metrics=distance_metrics,
        model_name=model,
    )
