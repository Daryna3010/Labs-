import datetime
import os
import re
import urllib.request
from urllib.error import URLError
import pandas as pd
import streamlit as st
import time
import numpy as np

class DataLoader:
    def __init__(self, reload_on_conflict, start_year=1981, end_year=2024):
        self._regions = { 
            1: ('Вінницька', 24),  2: ('Волинська', 25),  3: ('Дніпропетровська', 5),  4: ('Донецька', 6),
            5: ('Житомирська', 27),  6: ('Закарпатська', 23),  7: ('Запорізька', 26),  8: ('Івано-Франківська', 7),
            9: ('Київська', 11),  10: ('Кіровоградська', 13),  11: ('Луганська', 14),  12: ('Львівська', 15),
            13: ('Миколаївська', 16),  14: ('Одеська', 17),  15: ('Полтавська', 18),  16: ('Рівненська', 19),
            17: ('Сумська', 21),  18: ('Тернопільська', 22),  19: ('Харківська', 8),  20: ('Херсонська', 9),
            21: ('Хмельницька', 10),  22: ('Черкаська', 1),  23: ('Чернівецька', 3),  24: ('Чернігівська', 2),
            25: ('Республіка Крим', 4)
        }
        self.start_year = start_year
        self.end_year = end_year
        self.__data_folder = 'csvs'
        self.reload_on_conflict = reload_on_conflict
        self.load_csvs()
        self.df = self.create_df(self.__data_folder)

    def mkdir(self, name):
        path = os.path.join(os.getcwd(), name)
        if not os.path.isdir(path):
            os.mkdir(path)

    @staticmethod
    def remove_html_tags(text):
        pattern = re.compile('<.*?>')
        return re.sub(pattern, '', text)

    def load_csvs(self):
        for value in self._regions.values():
            self.download_csv(value[1], self.start_year, self.end_year)

    def download_csv(self, region_index, start_year, end_year):
        csvs_dir = self.__data_folder
        self.mkdir(csvs_dir)

        # Перевірка, чи є вже файл для цього регіону
        for file in os.listdir(os.path.join(os.getcwd(), csvs_dir)):
            if f'vhi_{region_index}_' in file:
                if self.reload_on_conflict:
                    os.remove(file)
                else:
                    return os.path.join(csvs_dir, file)

        # Формування URL для завантаження файлу
        url = f'https://www.star.nesdis.noaa.gov/smcd/emb/vci/VH/get_TS_admin.php?country=UKR&provinceID={region_index}&year1={start_year}&year2={end_year}&type=Mean'
        try:
            with urllib.request.urlopen(url) as wp:
                data = wp.read()
        except URLError as e:
            print(f"URL Error: {e}")
            return None

        current_time = datetime.datetime.now().strftime("%d%m%Y%H%M%S")
        file_name = os.path.join(csvs_dir, f'vhi_{region_index}_{current_time}.csv')

        try:
            with open(file_name, 'wb') as out:
                out.write(data)
        except IOError as e:
            print(f"File Error: {e}")
            return None

        return file_name

    def parse_csv(self, path, key, region):
        headers = ['Year', 'Week', 'SMN', 'SMT', 'VCI', 'TCI', 'VHI']
        df = pd.read_csv(path, index_col=False, header=1, names=headers)

        df.loc[0, "Year"] = self.remove_html_tags(df['Year'][0])

        column_na = df.isnull().sum()

        if column_na.sum() > 0:
            df.dropna(inplace=True)

        column_na_neg_one_indexes = df.loc[df['VHI'] == -1].index
        neg_one_am = len(column_na_neg_one_indexes)

        if neg_one_am > 0:
            df.drop(column_na_neg_one_indexes, inplace=True)

        df['Year'] = df['Year'].astype(int)
        df['Week'] = df['Week'].astype(int)

        df.insert(0, "RID", key)

        return df

    def create_df(self, data_folder):
        region_frames = []
        files = os.listdir(data_folder)

        for key in self._regions:
            value = self._regions[key]
            file_name = next((name for name in files if f"_{value[1]}_" in name), None)
            if not file_name:
                continue

            df = self.parse_csv(os.path.join(data_folder, file_name), key, value)

            region_frames.append(df)

        return pd.concat(region_frames).reset_index(drop=True)

class TablePage:

    def __init__(self):
        st.set_page_config(page_title="lab3")
        st.markdown("# Аналіз VHI даних")
        st.markdown("## Лабораторна робота 3")

        st.sidebar.header("Data Filters")
        self.data_loader = DataLoader(reload_on_conflict=False)

        # Dropdown для вибору типу даних (VCI, TCI, VHI)
        self.data_type = st.sidebar.selectbox("Select data type", ['VCI', 'TCI', 'VHI'])

        # Dropdown для вибору регіону
        self.region = st.sidebar.selectbox("Select region", list(self.data_loader._regions.values())) 

        # Slider для вибору діапазону тижнів
        self.week_range = st.sidebar.slider("Select week range", 1, 52, (1, 52))

        # Slider для вибору діапазону років
        self.year_range = st.sidebar.slider("Select year range", self.data_loader.start_year, self.data_loader.end_year, (self.data_loader.start_year, self.data_loader.end_year))

        # Чекбокси для сортування
        self.sort_asc = st.sidebar.checkbox('Sort Ascending')
        self.sort_desc = st.sidebar.checkbox('Sort Descending')

        # Кнопка для скидання фільтрів
        if st.sidebar.button("Reset Filters"):
            self.data_type = 'VCI'
            self.region = self.data_loader._regions[1]
            self.week_range = (1, 52)
            self.year_range = (self.data_loader.start_year, self.data_loader.end_year)
            self.sort_asc = False
            self.sort_desc = False

        # Три вкладки
        tab1, tab2, tab3 = st.tabs(["Таблиця", "Графік за обраною областю", "Порівняння між областями"])

        with tab1:
            self.table_tab()

        with tab2:
            self.plot_for_region()

        with tab3:
            self.plot_comparison()

    def sort_data(self, df):
        if self.sort_asc and self.sort_desc:
            st.warning("Cannot sort in both directions simultaneously. Default sorting will be applied.")
            return df.sort_values(by=['Year', 'Week']) 
        if self.sort_asc:
            return df.sort_values(by=self.data_type)
        if self.sort_desc:
            return df.sort_values(by=self.data_type, ascending=False)
        return df 

    def table_tab(self):
        filtered_df = self.data_loader.df[
            (self.data_loader.df['Year'] >= self.year_range[0]) &
            (self.data_loader.df['Year'] <= self.year_range[1]) &
            (self.data_loader.df['Week'] >= self.week_range[0]) &
            (self.data_loader.df['Week'] <= self.week_range[1]) &
            (self.data_loader.df['RID'] == self.region[1])
        ]
        
        sorted_df = self.sort_data(filtered_df)

        st.write(sorted_df)

    def plot_for_region(self):
        filtered_df = self.data_loader.df[
            (self.data_loader.df['Year'] >= self.year_range[0]) &
            (self.data_loader.df['Year'] <= self.year_range[1]) &
            (self.data_loader.df['Week'] >= self.week_range[0]) &
            (self.data_loader.df['Week'] <= self.week_range[1]) &
            (self.data_loader.df['RID'] == self.region[1])
        ]

        sorted_df = self.sort_data(filtered_df)

        st.line_chart(sorted_df[self.data_type])

    def plot_comparison(self):
        comparison_df = self.data_loader.df[self.data_loader.df['Year'] >= self.year_range[0]]
        comparison_df = comparison_df[comparison_df['Year'] <= self.year_range[1]]

        st.write(f"Comparison of {self.data_type} across regions")

        sorted_comparison_df = self.sort_data(comparison_df)

        comparison_pivot = sorted_comparison_df.pivot_table(
            index='Year', columns='RID', values=self.data_type
        )
        st.line_chart(comparison_pivot)

if __name__ == "__main__":
    TablePage()


