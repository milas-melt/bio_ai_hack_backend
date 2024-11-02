import pandas as pd

input = {
    "Age": 25,
    "Type II Diabetic": "Yes",
    "Ethnicity": "Asian or Asian British",
    "Sex": "Male",
}


df = pd.read_csv("/teamspace/studios/this_studio/repos/bio_ai_hack_backend/ozempic_side_effects_df_v0.csv")

filtered_df = df[(df["Age"] == input["Age"]) & 
                  #(df["Type II Diabetic"] == input["Type II Diabetic"]) & 
                  #(df["Ethnicity"] == input["Ethnicity"]) &
                  (df["Sex"] == input["Sex"])
                ]

print(len(filtered_df))
