# Instructions to get started

```bash
mkdir bio_ai_hack
cd bio_ai_hack
```

Then you git clone the backend repo

```bash
cd bio_ai_hack_backend
pip install -r requirements.txt
cd ..
python bio_ai_hack_backend/app.py
```

Rename .env_example to .env and put your OpenAI API key in it.

Then you can test the server:

```bash
http://127.0.0.1:5050/dashboard?age=55&weight=67&sex=M
```

The output will be a JSON object with the results.
e.g.,

```JSON
{
  "actionable_insights": [
    "a",
    "b",
    "c"
  ],
  "patient_info": {
    "age": "55",
    "ethnicity": null,
    "sex": "M",
    "weight": "67"
  },
  "probabilities": {
    "most_common": [
      [
        "age weight sex",
        []
      ],
      [
        "age",
        [
          [
            "Nausea",
            0.17049180327868851
          ],
          [
            "Vomiting",
            0.16557377049180327
          ],
          [
            "Impaired gastric emptying",
            0.15245901639344261
          ],
          [
            "Diarrhoea",
            0.10983606557377049
          ],
          [
            "Off label use",
            0.09508196721311475
          ],
          [
            "Constipation",
            0.06393442622950819
          ],
          [
            "Abdominal pain",
            0.06393442622950819
          ],
          [
            "Headache",
            0.06229508196721312
          ]
        ]
      ],
      [
        "sex",
        [
          [
            "Nausea",
            0.10484848484848484
          ],
          [
            "Off label use",
            0.0993939393939394
          ],
          [
            "Diarrhoea",
            0.09878787878787879
          ],
          [
            "Weight decreased",
            0.09696969696969697
          ],
          [
            "Decreased appetite",
            0.07696969696969697
          ],
          [
            "Vomiting",
            0.0703030303030303
          ],
          [
            "Constipation",
            0.06121212121212121
          ],
          [
            "Wrong technique in product usage process",
            0.058787878787878785
          ]
        ]
      ],
      [
        "weight",
        [
          [
            "Nausea",
            0.1346153846153846
          ],
          [
            "Off label use",
            0.11538461538461539
          ],
          [
            "Product use in unapproved indication",
            0.11538461538461539
          ],
          [
            "Weight decreased",
            0.09615384615384616
          ],
          [
            "Vomiting",
            0.09615384615384616
          ],
          [
            "Dizziness",
            0.07692307692307693
          ],
          [
            "Eye pain",
            0.057692307692307696
          ],
          [
            "Sepsis",
            0.057692307692307696
          ]
        ]
      ]
    ]
  },
  "testimony": "- User experienced nausea and dizziness after starting Ozempic.\n- Frequent headaches were reported.\n- There was significant fatigue, especially in the first few weeks.\n- User noticed a significant decrease in appetite.\n- Digestive issues were present, including constipation.\n- A skin rash was observed which wasn't present before.\n- Unusual food cravings were reported after taking Ozempic.\n- Moments of lightheadedness were experienced post-injections.\n- User had trouble sleeping at night, which was unexpected.\n- Despite weight loss, some stomach discomfort was experienced."
}
```
