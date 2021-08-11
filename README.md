Repository to create an interactive dashboard using DASH Plotly to visualize crimes in the Chicago city.

There are 3 main data files that this application uses: 

1) **all_data.csv** (stored in SQLite. You will not find it here! But we can achieve it performing the manipulations below)
2) **boundaries**
3) **m.csv**

A screenshot of the *all_data* data frame (all primary modifications to obtain the used tables were made using **Kaggle** environment):
![Data frame](https://github.com/danielfurlan/chicago_crimes/blob/master/images/df_alldata.png)

The main source for the crimes statistics comes from here : [kaggle!](https://www.kaggle.com/chicago/chicago-crime) 

From that file, we can achieve the 1) and 3) data that we use by doing **Extraction** and **Transformation**.

These are some of the first columns that this file contains:
![Data frame](https://github.com/danielfurlan/chicago_crimes/blob/master/images/df_chicago.png)

In order to create new columns disposing data such as *quantity of crimes occured in some particular location (e.g. RESIDENCE) in a certain distric* we need to operate some code!

Using **pandas** and **numpy** libraries we can achieve that:
![beats](https://github.com/danielfurlan/chicago_crimes/blob/master/images/beats_chicago.png)

To calculate the number of crimes with respect to *Location*, *District* and *date*, we just need to perfomr some **group_by** in pararel with **transform (count)**
![columns](https://github.com/danielfurlan/chicago_crimes/blob/master/images/columns_chicago.png)

Using the **all_data** table, we are able to perform some SQL queries in the dataset that is stored in a SQLite database.

2 main queries are perfomed when user interacts with the app:
```
query = """select "District","date","Districtperday" as "total crimes" 
          from crimes_alldata 
          where "District" in {} and "date" between '{}' and '{}' 
          group by "District", "date", "Districtperday" """.format(sel_districts,start,end)
```

and:

```
query = """select "District", "LocationDescription", sum("total") as "TOTAL" 
        from (
                select "District","date", "LocationDescription", count("Location/Distrperday") as total 
                        from crimes_alldata 
                        where "District" in {} and "date" between '{}' and '{}' and "LocationDescription" in {}
                        group by "District", "LocationDescription","date", "Location/Distrperday") as sss
        group by "District", "LocationDescription" """.format(sel_districts,start,end,str_locations)

```
