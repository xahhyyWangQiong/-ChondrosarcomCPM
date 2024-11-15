import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import torch
from pycox.models import CoxPH
# from models.cox import CoxPH
st.set_page_config(layout="wide")

def data_porcess(data):
    age, tumor_size = data[:2]
    age_mean = 52.18131868
    age_scale = 17.87908795
    tumor_size_mean = 79.69853876
    tumor_size_scale = 45.40890953
    age = (age - age_mean) / age_scale
    tumor_size = (tumor_size - tumor_size_mean) / tumor_size_scale
    return [age, tumor_size] + data[2:]

def get_deepsurv_model():
    in_features = 9 
    out_features = 1 

    net = torch.nn.Sequential(
        torch.nn.Linear(in_features, 64),
        torch.nn.ReLU(),
        torch.nn.BatchNorm1d(64),
        torch.nn.Dropout(0.147),
        
        torch.nn.Linear(64, 64),
        torch.nn.ReLU(),
        torch.nn.BatchNorm1d(64),
        torch.nn.Dropout(0.147),
        
        torch.nn.Linear(64, out_features),
        
    )
    model = CoxPH(net)
    return model

@st.cache_data(show_spinner=False)
# @st.cache(show_spinner=False)
def load_setting():
    settings = {
        'Age': {'values': [0, 100], 'type': 'slider', 'init_value': 50, 'add_after': ', year'},
        'Gender': {'values': ["Male", "Female"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Primary site': {'values': ["Extremity", "Axial skeleton", "Other"], 'type': 'selectbox', 'init_value': 1, 'add_after': ''},
        'Histological type': {'values': ["Conventional", "Dedifferentiated"], 'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Grade': {
            'values': ["Well differentiated", "Moderately differentiated", "Poorly differentiated", 'Undifferentiated'],
            'type': 'selectbox', 'init_value': 0, 'add_after': ''},
        'Surgery': {'values': ["None", "Local treatment", "Radical excision with limb salvage", 'Amputation'],
                    'type': 'selectbox', 'init_value': 1, 'add_after': ''},
        'Tumor size': {'values': [0, 1000], 'type': 'slider', 'init_value': 135, 'add_after': ', mm'},
        'Tumor extension': {'values': ["No break in periosteum", "Extension beyond periosteum", "Further extension"],
                            'type': 'selectbox', 'init_value': 1, 'add_after': ''},
        'Distant metastasis': {'values': ["None", "Yes"], 'type': 'selectbox',
                               'init_value': 0,
                               'add_after': ''}
    }


    input_keys = ['Age', 'Tumor size', 'Gender','Histological type','Primary site',  'Grade', 'Surgery', 'Tumor extension', 'Distant metastasis']
    return settings, input_keys


settings, input_keys = load_setting()


# @st.cache_data(show_spinner=False)
# def get_model():
#     deepsurv_model = get_deepsurv_model()
#     deepsurv_model.load_model_weights(path="weights")
#     deepsurv_model.load_net('nets.pt')
#     return deepsurv_model


def get_code():
    sidebar_code = []
    for key in settings:
        if settings[key]['type'] == 'slider':
            sidebar_code.append(
                "{} = st.slider('{}',{},{},key='{}')".format(
                    key.replace(' ', '____'),
                    key + settings[key]['add_after'],
                    # settings[key]['values'][0],
                    ','.join(['{}'.format(value) for value in settings[key]['values']]),
                    settings[key]['init_value'],
                    key
                )
            )
        if settings[key]['type'] == 'selectbox':
            sidebar_code.append('{} = st.selectbox("{}",({}),{},key="{}")'.format(
                key.replace(' ', '____'),
                key + settings[key]['add_after'],
                ','.join('"{}"'.format(value) for value in settings[key]['values']),
                settings[key]['init_value'],
                key
            )
            )
    return sidebar_code




# print('\n'.join(sidebar_code))
if 'patients' not in st.session_state:
    st.session_state['patients'] = []
if 'display' not in st.session_state:
    st.session_state['display'] = 1
if 'model' not in st.session_state:
    st.session_state['model'] = 'deepsurv'


sidebar_code = get_code()
def plot_survival():
    pd_data = pd.concat(
        [
            pd.DataFrame(
                {
                    'Survival': item['survival'],
                    'Time': item['times'],
                    'Patients': [item['No'] for i in item['times']]
                }
            ) for item in st.session_state['patients']
        ]
    )
    if st.session_state['display']:
        fig = px.line(pd_data, x="Time", y="Survival", color='Patients', range_y=[0, 1])
    else:
        fig = px.line(pd_data.loc[pd_data['Patients'] == pd_data['Patients'].to_list()[-1], :], x="Time", y="Survival",
                      range_y=[0, 1])
    fig.update_layout(template='simple_white',
                      title={
                          'text': 'Estimated Survival Probability',
                          'y': 0.9,
                          'x': 0.5,
                          'xanchor': 'center',
                          'yanchor': 'top',
                          'font': dict(
                              size=25
                          )
                      },
                      plot_bgcolor="white",
                      xaxis_title="Time, month",
                      yaxis_title="Survival probability",
                      )
    st.plotly_chart(fig, use_container_width=True)


def plot_patients():
    patients = pd.concat(
        [
            pd.DataFrame(
                dict(
                    {
                        'Patients': [item['No']],
                        '1-Year': ["{:.2f}%".format(item['1-year'] * 100)],
                        '3-Year': ["{:.2f}%".format(item['3-year'] * 100)],
                        '5-Year': ["{:.2f}%".format(item['5-year'] * 100)]
                    },
                    **item['arg']
                )
            ) for item in st.session_state['patients']
        ]
    ).reset_index(drop=True)
    st.dataframe(patients)

deepsurv_model = get_deepsurv_model()
# _ = deepsurv_model.compute_baseline_hazards()
# deepsurv_model.load_net('nets.pt')
deepsurv_model.load_model_weights(path="weights")
# deepsurv_model.load_net('nets.pt')
# _ = deepsurv_model.compute_baseline_hazards()
# deepsurv_model.compute_baseline_hazards()
# @st.cache(show_spinner=True)
def predict():
    print('update patients . ##########')
    print(st.session_state)
    input = []
    for key in input_keys:
        value = st.session_state[key]
        if isinstance(value, int):
            input.append(value)
        if isinstance(value, str):
            input.append(settings[key]['values'].index(value))
    
    input = data_porcess(input)
    input = np.expand_dims(np.array(input, dtype=np.float32), 0)
    survival = deepsurv_model.predict_surv_df(input)
    survival = np.array(survival)

    data = {
        'survival': survival.flatten(),
        'times': [i for i in range(0, len(survival.flatten()))],
        'No': len(st.session_state['patients']) + 1,
        'arg': {key:st.session_state[key] for key in input_keys},
        '1-year': survival[12, 0],
        '3-year': survival[36, 0],
        '5-year': survival[60, 0]
    }
    st.session_state['patients'].append(
        data
    )
    print('update patients ... ##########')

def plot_below_header():
    col1, col2 = st.columns([1, 9])
    col3, col4, col5, col6, col7 = st.columns([2, 2, 2, 2, 2])
    with col1:
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        st.write('')
        # st.session_state['display'] = ['Single', 'Multiple'].index(
        #     st.radio("Display", ('Single', 'Multiple'), st.session_state['display']))
        st.session_state['display'] = ['Single', 'Multiple'].index(
            st.radio("Display", ('Single', 'Multiple'), st.session_state['display']))
        # st.radio("Model", ('DeepSurv', 'NMTLR','RSF','CoxPH'), 0,key='model',on_change=predict())
    with col2:
        plot_survival()
    with col4:
        st.metric(
            label='1-Year survival probability',
            value="{:.2f}%".format(st.session_state['patients'][-1]['1-year'] * 100)
        )
    with col5:
        st.metric(
            label='3-Year survival probability',
            value="{:.2f}%".format(st.session_state['patients'][-1]['3-year'] * 100)
        )
    with col6:
        st.metric(
            label='5-Year survival probability',
            value="{:.2f}%".format(st.session_state['patients'][-1]['5-year'] * 100)
        )
    st.write('')
    st.write('')
    st.write('')
    plot_patients()
    st.write('')
    st.write('')
    st.write('')
    st.write('')
    st.write('')

st.header('DeepSurv-based model for predicting survival of chondrosarcoma', anchor='survival-of-chondrosarcoma')
if st.session_state['patients']:
    plot_below_header()
st.subheader("Instructions:")
st.write("1. Select patient's infomation on the left\n2. Press predict button\n3. The model will generate predictions")
st.write('***Note: this model is still a research subject, and the accuracy of the results cannot be guaranteed!***')
st.write("***[Paper link](https://pubmed.ncbi.nlm.nih.gov/)(To be updated)***")
with st.sidebar:
    with st.form("my_form",clear_on_submit = False):
        for code in sidebar_code:
            exec(code)
        col8, col9, col10 = st.columns([3, 4, 3])
        with col9:
            prediction = st.form_submit_button(
                'Predict',
                on_click=predict,
                # args=[{key: eval(key.replace(' ', '____')) for key in input_keys}]
            )

