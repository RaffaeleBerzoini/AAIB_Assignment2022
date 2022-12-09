import numpy as np
import pandas as pd
from tensorflow import keras
from sklearn.model_selection import StratifiedKFold
import cv2

PATH_NORMAL = 'dataset/normal'
PATH_PNEUMONIA = 'dataset/pneumonia'
PATH_TUBERCULOSIS = 'dataset/tuberculosis'

NORMAL = 0
PNEUMONIA = 1
TUBERCULOSIS = 2


class DataGen(keras.utils.Sequence):

    def __init__(self, batch_size, img_size, input_paths, target):
        self.batch_size = batch_size
        self.img_size = img_size  # (400, 400)
        self.input_img_paths = input_paths
        self.target = target
        self.directory = 'dataset/'

    def __getitem__(self, index):
        i = index * self.batch_size
        batch_input_img_paths = self.input_img_paths[i: i + self.batch_size]
        batch_target = self.target[i: i + self.batch_size]
        x = np.zeros((self.batch_size,) + self.img_size + (1,))
        y = np.zeros((self.batch_size,) + (3,))

        for j, path in enumerate(batch_input_img_paths):
            img = cv2.imread(self.directory + path, 0)  # read as grayscale
            img = cv2.resize(img, self.img_size, interpolation=cv2.INTER_CUBIC)
            x[j] = np.expand_dims(img, 2)

        for i in range(len(y)):
            y[i][batch_target[i] - 1] = 1

        return x, y

    def __len__(self):
        return len(self.target) // self.batch_size


def make_list_of_patients():
    data = pd.read_csv('dataset/labels_train.csv', sep=',')

    patients = pd.DataFrame(columns=['ID', 'paths', 'label'])

    for _, row in data.iterrows():
        patient_ID = row['file'].split('_')[0]
        if len(patients.loc[patients['ID'] == patient_ID, 'paths']) == 0:
            new_patient = {'ID': patient_ID, 'paths': row['file'], 'label': row['label']}
            patients = patients.append(new_patient, ignore_index=True)
        else:
            old_label = patients.loc[patients['ID'] == patient_ID, 'label']
            assert old_label.values[0] == row['label']  # make sure two samples with the same ID do not have
            # different diagnosis
            paths = patients.loc[patients['ID'] == patient_ID, 'paths'].to_list()
            paths.append(row['file'])
            updated_patient = {'ID': patient_ID, 'paths': paths, 'label': row['label']}
            patients.drop(patients[patients.ID == patient_ID].index, inplace=True)
            patients = patients.append(updated_patient, ignore_index=True)

    patients = patients.replace('N', NORMAL)
    patients = patients.replace('P', PNEUMONIA)
    patients = patients.replace('T', TUBERCULOSIS)
    return patients


def cross_validation_splits(data: pd.DataFrame, fold=5, shuffle=True, random_state=8432):
    X = data.iloc[:, :-1].values
    y = data.iloc[:, -1].values

    skf = StratifiedKFold(n_splits=fold, shuffle=shuffle, random_state=random_state)

    X_train_folds = []
    y_train_folds = []

    X_test_folds = []
    y_test_folds = []
    for i, (train_index, test_index) in enumerate(skf.split(X, y)):
        X_train = []
        y_train = []
        X_test = []
        y_test = []
        for idx_train in train_index:
            if len(data.iloc[idx_train, 1]) > 1 and type(data.iloc[idx_train, 1]) == list:
                for element in data.iloc[idx_train, 1]:
                    X_train.append(element)
                    y_train.append(data.iloc[idx_train, 2])
            else:
                X_train.append(data.iloc[idx_train, 1])
                y_train.append(data.iloc[idx_train, 2])

        X_train_folds.append(X_train)
        y_train_folds.append(y_train)

        for idx_test in test_index:
            if len(data.iloc[idx_test, 1]) > 1:
                for element in data.iloc[idx_test, 1]:
                    X_test.append(element)
                    y_test.append(data.iloc[idx_test, 2])
            else:
                X_test.append(data.iloc[idx_test, 1])
                y_test.append(data.iloc[idx_test, 2])

        X_test_folds.append(X_test)
        y_test_folds.append(y_test)

    return X_train_folds, y_train_folds, X_test_folds, y_test_folds


if __name__ == '__main__':
    # usage example

    pat = make_list_of_patients()
    X_train_folds, y_train_folds, X_test_folds, y_test_folds = cross_validation_splits(data=pat)

    x_train_fold0 = X_train_folds[0]
    y_train_fold0 = y_train_folds[0]

    x_test_fold0 = X_test_folds[0]
    y_test_fold0 = y_test_folds[0]

    dg0 = DataGen(2, (256, 256), x_train_fold0, y_train_fold0)

    x_batch_2, y_batch_2 = dg0.__getitem__(2)