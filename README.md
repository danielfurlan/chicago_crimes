Repository to create an interactive dashboard using DASH Plotly to visualize crimes in the Chicago city.

There are 3 main data files that this application uses: 

1) **all_data.csv**: 
2) **Boundaries**
3) **m.csv**

The main source for the crimes statistics come from here : ![kaggle!](https://www.kaggle.com/chicago/chicago-crime) 

From that file, we can achieve the 1) and 3) data that we use by doing **Extraction** and **Transformation**.

These are some of the first columns that this file contains:
![Data frame](https://github.com/danielfurlan/chicago_crimes/blob/master/images/df_chicago.png)

In order to create new columns disposing data such as *quantity of crimes occured in some particular location (e.g. RESIDENCE) in a certain distric* we need to operate some code!

Using **pandas** and **numpy** libraries we can achieve that:
![beats](https://github.com/danielfurlan/chicago_crimes/blob/master/images/beats_chicago.png)

To calculate the number of crimes with respect to *Location*, *District* and *date*, we just need to perfomr some **group_by** in pararel with **transform (count)**
![columns](https://github.com/danielfurlan/chicago_crimes/blob/master/images/columns_chicago.png)
