# -*- coding: utf-8 -*-
"""baseline.ipynb

Automatically generated by Colaboratory.

Original file is located at my google drive :)

# Baseline
"""

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

# !pip freeze | grep "numpy\|pandas\|lightgbm\|scikit-learn"

"""## Загрузка данных"""

train_df = pd.read_parquet("train_data.pqt")
test_df = pd.read_parquet("test_data.pqt")

train_df.head(9)

test_df.head(9)

cat_cols = [
    "channel_code", "city", "city_type",
    "okved", "segment", "start_cluster",
    "index_city_code", "ogrn_month", "ogrn_year",
]

"""Обозначение категориальных признаков"""

train_df[cat_cols] = train_df[cat_cols].astype("category")
test_df[cat_cols] = test_df[cat_cols].astype("category")

"""Создаем выборки для валидации и обучения"""

X = train_df.drop(["id", "date", "end_cluster"], axis=1)
y = train_df["end_cluster"]

x_train, x_val, y_train, y_val = train_test_split(X, y,
                                                  test_size=0.1,
                                                  random_state=42)

X

"""## Обучение модели

В качестве базовой модели возьмем LGBM обучим на всех признаках
"""

model = LGBMClassifier(verbosity=-1, random_state=42, n_jobs=-1)
model.fit(x_train, y_train)

"""Зададим функцию для взвешенной метрики roc auc"""

def weighted_roc_auc(y_true, y_pred, labels, weights_dict):
    unnorm_weights = np.array([weights_dict[label] for label in labels])
    weights = unnorm_weights / unnorm_weights.sum()
    classes_roc_auc = roc_auc_score(y_true, y_pred, labels=labels,
                                    multi_class="ovr", average=None)
    return sum(weights * classes_roc_auc)

cluster_weights = pd.read_excel("cluster_weights.xlsx").set_index("cluster")
weights_dict = cluster_weights["unnorm_weight"].to_dict()

"""Проверка работы модели"""

y_pred_proba = model.predict_proba(x_val)
y_pred_proba.shape

weighted_roc_auc(y_val, y_pred_proba, model.classes_, weights_dict)

"""## Прогноз на тестовой выборке"""

test_df.pivot(index="id", columns="date", values="start_cluster").head(3)

"""Для того, чтобы сделать прогноз на тестовой выборке, нужно заполнить стартовый кластер. </br>
В качестве базового подхода заполним все стартовые кластеры, самым популярным кластером.
"""

test_df["start_cluster"] = train_df["start_cluster"].mode()[0]
test_df["start_cluster"] = test_df["start_cluster"].astype("category")

sample_submission_df = pd.read_csv("sample_submission.csv")

sample_submission_df.shape

sample_submission_df.head()

# @title id

# from matplotlib import pyplot as plt
# sample_submission_df['id'].plot(kind='line', figsize=(8, 4), title='id')
# plt.gca().spines[['top', 'right']].set_visible(False)

"""Для тестовой выборки будем использовать только последний месяц"""

last_m_test_df = test_df[test_df["date"] == "month_6"]
last_m_test_df = last_m_test_df.drop(["id", "date"], axis=1)

test_pred_proba = model.predict_proba(last_m_test_df)
test_pred_proba_df = pd.DataFrame(test_pred_proba, columns=model.classes_)
sorted_classes = sorted(test_pred_proba_df.columns.to_list())
test_pred_proba_df = test_pred_proba_df[sorted_classes]

test_pred_proba_df.shape

test_pred_proba_df.head(2)

sample_submission_df[sorted_classes] = test_pred_proba_df
sample_submission_df.to_csv("baseline_submission.csv", index=False)

r = pd.read_csv('baseline_submission.csv')
r