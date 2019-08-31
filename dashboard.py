# -*- coding: UTF-8 -*-

import dash
import dash_table
import plotly.graph_objects as go
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import re

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Visualizing Swiggy Order History"

server = app.server

get_lat = lambda x: float(x.split(',')[0])
get_lng = lambda x: float(x.split(',')[1])

def seriesToFrame(se, cols):
    se=se.to_frame().reset_index(level=0, inplace=False)
    se.columns=cols
    return se

def dis_round(val, is_cur=False):
    if is_cur:
        return str(re.sub("(\d)(?=(\d{3})+(?!\d))", r"\1,", "%d" % np.round_(val, decimals=2)))
    else:
        return str(np.round_(val, decimals=2))

def getTimeCategory(se):
    sr = list()
    for x in se:
        if(x.hour<6):
            sr.append("Late Night (12AM to 6AM)")
            continue
        elif(x.hour<12):
            sr.append("Morning (6AM to 12PM)")
            continue
        elif(x.hour<18):
            sr.append("Afternoon (12PM to 6PM)")
            continue
        else:
            sr.append("Night (6PM to 12AM)")
    return pd.Series(sr) 


df=pd.read_json("order_data.txt")
cum_se = df['order_total'].cumsum()
df['cum_order_sum'] = (cum_se.sort_values(ascending =False, inplace=False)).reset_index()['order_total']

cum_re = df['restaurant_customer_distance'].cumsum()
df['restaurant_customer_distance_cum'] = (cum_re.sort_values(ascending =False, inplace=False)).reset_index()['restaurant_customer_distance']

cum_se_res = df['order_restaurant_bill'].cumsum()
df['cum_order_sum_res'] = (cum_se_res.sort_values(ascending =False, inplace=False)).reset_index()['order_restaurant_bill']

df['delivery_time_in_hours']=df['delivery_time_in_seconds']/3600.0

total_orders = len(df)

order_time_series = df['order_time']
order_zone_series = getTimeCategory(order_time_series)
order_zone_series = order_zone_series.value_counts(dropna=False)

on_time_series = df["on_time"].astype('int64')
on_time_series = on_time_series.astype('bool')
on_time_series = on_time_series.value_counts(dropna=False)

total_duration = order_time_series[0]-order_time_series[total_orders-1]

mid_time = order_time_series[total_orders-1]+(total_duration)/2
first_half_orders = order_time_series[order_time_series<mid_time].count()


special_fee = df['special_fee'].value_counts(dropna=False)
time_fee = df['time_fee'].value_counts(dropna=False)
distance_fee = df['distance_fee'].value_counts(dropna=False)
threshold_fee = df['threshold_fee'].value_counts(dropna=False)

special_fee = seriesToFrame(special_fee, ['Money','Count'])
time_fee = seriesToFrame(time_fee, ['Money','Count'])
distance_fee = seriesToFrame(distance_fee, ['Money','Count'])
threshold_fee = seriesToFrame(threshold_fee, ['Money','Count'])

restaurant_city_name = df['restaurant_city_name'].value_counts(dropna=False)
restaurant_coverage_area = df['restaurant_coverage_area'].value_counts(dropna=False)

restaurant_name = df['restaurant_name'].value_counts(dropna=False)
restaurant_name = seriesToFrame(restaurant_name, ['Restaurant Name','Order Count'])

restaurant_type = df['restaurant_type'].value_counts(dropna=False)
restaurant_type = seriesToFrame(restaurant_type, ['Restaurant Category Code','Order Count'])


is_coupon_applied = df['is_coupon_applied'].value_counts(dropna=False)
coupon_type = df['coupon_type'].value_counts(dropna=True)

coupon_applied = df['coupon_applied'].value_counts(dropna=False)
coupon_applied = seriesToFrame(coupon_applied, ['Coupon Code','Order Count'])

payment_method = df['payment_method'].value_counts(dropna=False)
payment_method = seriesToFrame(payment_method, ['Payment Method','Order Count'])

order_payment_method = df['order_payment_method'].value_counts(dropna=False)
order_payment_method = seriesToFrame(order_payment_method, ['Specific Payment Method','Order Count'])

customer_user_agent = df['customer_user_agent'].value_counts(dropna=False)
customer_user_agent = seriesToFrame(customer_user_agent, ['Client Type','Order Count'])

# df['restaurant_lat'] = df['restaurant_lat_lng'].astype(str).map(get_lat)
# df['restaurant_lng'] = df['restaurant_lat_lng'].astype(str).map(get_lng)

lat=list()
lng=list()
for x in df['restaurant_lat_lng']:
    try:
        lat.append(float(x.split(',')[0]))
    except:
        lat.append(0.0)
    try:
        lng.append(float(x.split(',')[1]))
    except:
        lng.append(0.0)

lat = pd.Series(lat).value_counts()
lng = pd.Series(lng).value_counts()

fig_map = go.Figure(go.Densitymapbox(lat=list(lat.index), lon=list(lng.index), z=lat.tolist(), radius=15))
fig_map.update_layout(mapbox_style="stamen-terrain", mapbox_center_lon=180, mapbox={'zoom':12, 'center':{'lat':lat.index[0], 'lon':lng.index[0]}})
fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

order_item_list=list()
for x in df['order_items']:
    order_item_list.extend(x)

order_df=pd.DataFrame.from_records(order_item_list)

item_name = order_df['name'].value_counts(dropna=False).head(10)
item_name = seriesToFrame(item_name, ['Item Name','Count'])

is_veg = order_df['is_veg']

is_veg_list = list()
for elem in is_veg:
    if elem == "0":
        is_veg_list.append("Non Veg")
        continue
    elif elem == "1":
        is_veg_list.append("Veg")
        continue
    else:
        is_veg_list.append("Other")

is_veg = pd.Series(is_veg_list).value_counts(dropna=False)

charges_list=list()
for x in df['charges']:
    charges_list.append(x)

charges_df=pd.DataFrame.from_records(charges_list)

fee_names = ["Vat","Service Charges","Service Tax","Delivery Charges","Packing Charges","Convenience Fee","Cancellation Fee","GST"]
fee_amount = list()

for fee_name in fee_names:
    fee_amount.append(charges_df[fee_name].astype(float).sum())

fee_df = pd.DataFrame(list(zip(fee_names, fee_amount)), columns =['Charge Type', 'Amount']) 

delivery_boy_list=list()
for x in df['delivery_boy']:
    if isinstance(x, dict):
        delivery_boy_list.append(x)

delivery_boy_list_df=pd.DataFrame.from_records(delivery_boy_list)

delivery_boy_name = delivery_boy_list_df['name'].value_counts(dropna=False)
delivery_boy_name = seriesToFrame(delivery_boy_name, ['Delivery Partner Name','Delivery Count']).head(10)


app.layout = html.Div(children=[
    html.H2(children='Midnight Hack Episode 1', style={'textAlign': 'center'}),

    html.H6(children='Visualizing Swiggy Order History - Sanat Dutta', style={'textAlign': 'center'}),

    html.A([
    html.Img(
                src='https://image.flaticon.com/icons/svg/1384/1384014.svg',
                style={
                    'height' : '36px',
                    'width' : '36px',

                },
            ),
    ], target='_blank', href='https://www.linkedin.com/in/sanatdutta/', style={
                    'height' : '36px',
                    'width' : '36px',
                    'float' : 'right',

                },),

    html.A([
    html.Img(
                src='https://image.flaticon.com/icons/svg/69/69366.svg',
                style={
                    'height' : '36px',
                    'width' : '36px',

                },
            ),
    ], target='_blank', href='https://www.instagram.com/sanatoverhere/', style={
                    'height' : '36px',
                    'width' : '36px',
                    'float' : 'right',

                },),

    html.A([
    html.Img(
                src='https://image.flaticon.com/icons/svg/69/69407.svg',
                style={
                    'height' : '36px',
                    'width' : '36px',

                },
            ),
    ], target='_blank', href='https://www.facebook.com/SanatOverHere', style={
                    'height' : '36px',
                    'width' : '36px',
                    'float' : 'right',

                },),

    html.A([
    html.Img(
                src='https://image.flaticon.com/icons/svg/109/109476.svg',
                style={
                    'height' : '36px',
                    'width' : '36px',

                },
            ),
    ], target='_blank', href='http://www.satandigital.com/', style={
                    'height' : '36px',
                    'width' : '36px',
                    'float' : 'right',

                },),

    dcc.Markdown('''
---
> You ordered a tolal of **'''+ str(total_orders) +'''** times.

> Your first order was on **'''+ str(df['order_time'][total_orders-1]) +'''** from **'''+ str(df['restaurant_name'][total_orders-1]) +''', '''+str(df['restaurant_area_name'][total_orders-1])+'''** and your last order was on **'''+ str(df['order_time'][0]) +'''** from **'''+ str(df['restaurant_name'][0]) +''', '''+str(df['restaurant_area_name'][0])+'''**
        '''),


    html.Div([
        html.Div([
            dcc.Graph(id='order_v_time', figure=go.Figure([go.Scatter(x=df['order_time'], y=df['order_total'])], layout=go.Layout(title=go.layout.Title(text="Order Amount vs Time"))))
        ], className="six columns"),

        html.Div([
            dcc.Graph(id='cum_order_v_time', figure=go.Figure([go.Scatter(x=df['order_time'], y=df['cum_order_sum'])], layout=go.Layout(title=go.layout.Title(text="Cumulative Order Amount vs Time"))))
        ], className="six columns"),

    ], className="row", style={'margin-top': '20px'}),

        dcc.Markdown('''
> The minimum order amount is **Rs. ''' + dis_round(df['order_total'].min()) + '''**, maximum order amount **Rs. ''' + dis_round(df['order_total'].max()) + '''** with an average of **Rs.''' + dis_round(df['order_total'].mean()) + '''**. The ordering frequency in first half is **'''+ str(first_half_orders) +'''** and in second half is **'''+ str(total_orders-first_half_orders) +'''**

> The total amount spent in past **'''+dis_round(total_duration.days/365.0)+''' years** is ** Rs. '''+dis_round(df['cum_order_sum'][0], True)+'''**

> The total restaurant bill is ** Rs. '''+dis_round(df['cum_order_sum_res'][0], True)+'''**. Total money saved via discounts is **'''+ dis_round(df['cum_order_sum_res'][0]-df['cum_order_sum'][0], True) +'''**

---
        '''),


    html.Div([
        html.Div([
            dcc.Graph(id='restaurant_city_name', figure=go.Figure([go.Pie(labels=list(restaurant_city_name.index), values=restaurant_city_name.tolist(), name='restaurant_city_name')], layout=go.Layout(title=go.layout.Title(text="City Wise Order Breakdown"))))
        ], className="six columns"),

        html.Div([
            dcc.Graph(id='restaurant_coverage_area', figure=go.Figure([go.Pie(labels=list(restaurant_coverage_area.index), values=restaurant_coverage_area.tolist(), name='restaurant_coverage_area')], layout=go.Layout(title=go.layout.Title(text="Area Wise Order Breakdown"))))
        ], className="six columns"),

    ], className="row", style={'margin-top': '20px'}),

    html.Div([
        html.H6('Restaurant Density Map'),
        html.Div([
            dcc.Graph(id='fig_map', figure=fig_map)
        ], className="twelve columns"),

    ], className="row", style={'margin-top': '20px'}),

    dcc.Markdown('''
---
        '''),

    html.Div([

        html.Div([
            dcc.Graph(id='restaurant_customer_distance_cum', figure=go.Figure([go.Scatter(x=df['order_time'], y=df['restaurant_customer_distance_cum'])], layout=go.Layout(title=go.layout.Title(text="Cumulative Distance Travelled by Delivery Partners vs Time"))))
        ], className="six columns"),

        html.Div([
            html.H6('Delivery Partner Delivery Count'),
            dash_table.DataTable(id='delivery_boy_name',columns=[{"name": i, "id": i} for i in delivery_boy_name.columns],data=delivery_boy_name.to_dict('records'),css=[{
        'selector': '.dash-cell div.dash-cell-value',
        'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
    }],
    style_cell={
        'whiteSpace': 'no-wrap',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'maxWidth': 0,
        'textAlign': 'center',
    },)
        ], className="three columns"),

    

        html.Div([
            html.H6('User Client Type'),
            dash_table.DataTable(id='customer_user_agent',columns=[{"name": i, "id": i} for i in customer_user_agent.columns],data=customer_user_agent.to_dict('records'),css=[{
        'selector': '.dash-cell div.dash-cell-value',
        'rule': 'display: inline; white-space: inherit; overflow: inherit; text-overflow: inherit;'
    }],
    style_cell={
        'whiteSpace': 'no-wrap',
        'overflow': 'hidden',
        'textOverflow': 'ellipsis',
        'maxWidth': 0,
        'textAlign': 'center',
    },)
        ], className="three columns"),

    ], className="row", style={'margin-top': '20px'}),


        dcc.Markdown('''

> The total distance travelled by delivery partners in past **'''+dis_round(total_duration.days/365.0)+''' years** is **'''+dis_round(df['restaurant_customer_distance_cum'][0], True)+''' kms**

> The total delivery time is **'''+dis_round(df['delivery_time_in_hours'].sum(), True)+''' hours** with maximum delivery time of **'''+dis_round(df['delivery_time_in_hours'].max()*60, True)+''' minutes** and average delivery time of **'''+dis_round(df['delivery_time_in_hours'].mean()*60, True)+''' minutes**

> **'''+str(delivery_boy_name['Delivery Partner Name'][0])+'''** has delivered to you **'''+ str(delivery_boy_name['Delivery Count'][0]) +''' times**

---
        '''),

    html.Div([
        html.Div([
            html.H6('Most Ordered Items'),
            dash_table.DataTable(id='item_name',columns=[{"name": i, "id": i} for i in item_name.columns],data=item_name.to_dict('records'),style_cell={'textAlign': 'center'},)
        ], className="six columns"),

        html.Div([
            dcc.Graph(id='is_veg', figure=go.Figure([go.Pie(labels=list(is_veg.index), values=is_veg.tolist(), name='is_veg')], layout=go.Layout(title=go.layout.Title(text="Item Type"))))
        ], className="six columns"),

    ], className="row", style={'margin-top': '20px'}),

    dcc.Markdown('''

> Your favorite item is **'''+str(item_name['Item Name'][0])+'''** 

---
        '''),

    html.Div([
        html.Div([
            html.H6('Restaurant Wise Order Breakdown'),
            dash_table.DataTable(id='restaurant_name',columns=[{"name": i, "id": i} for i in restaurant_name.columns],data=restaurant_name.head(n=10).to_dict('records'),style_cell={'textAlign': 'center'},)
        ], className="four columns"),

        html.Div([
            dcc.Graph(id='restaurant_name_bar', figure=go.Figure([go.Bar(x=restaurant_name.head(n=20)['Restaurant Name'].tolist(), y=restaurant_name.head(n=20)['Order Count'].tolist())]))
        ], className="four columns"),

        html.Div([
            html.H6('Restaurant Types'),
            dash_table.DataTable(id='restaurant_type',columns=[{"name": i, "id": i} for i in restaurant_type.columns],data=restaurant_type.head(n=10).to_dict('records'),style_cell={'textAlign': 'center'},)
        ], className="four columns"),

    ], className="row", style={'margin-top': '20px'}),

        dcc.Markdown('''

> Your favorite restaurant is **'''+ str(restaurant_name['Restaurant Name'][0]) +'''**

> Turns out they also have category codes for restaurants. Not sure what these codes actually mean. Let me know if anyone figures it out.

---
        '''),

    html.Div([
        html.Div([
            dcc.Graph(id='is_coupon_applied', figure=go.Figure([go.Pie(labels=list(is_coupon_applied.index), values=is_coupon_applied.tolist(), name='is_coupon_applied')], layout=go.Layout(title=go.layout.Title(text="Coupons Applied"))))
        ], className="six columns"),

        html.Div([
            dcc.Graph(id='coupon_type', figure=go.Figure([go.Pie(labels=list(coupon_type.index), values=coupon_type.tolist(), name='coupon_type')], layout=go.Layout(title=go.layout.Title(text="Coupon Types"))))
        ], className="six columns"),

    ], className="row", style={'margin-top': '20px'}),


    html.Div([

        html.Div([
            dcc.Graph(id='coupon_applied', figure=go.Figure([go.Bar(x=coupon_applied['Coupon Code'].tolist(), y=coupon_applied['Order Count'].tolist())], layout=go.Layout(title=go.layout.Title(text="Detailed Applied Coupon Breakdown"))))
        ], className="twelve columns"),

    ], className="row", style={'margin-top': '20px'}),

    dcc.Markdown('''

> Out of **'''+ str(total_orders) +''' orders**, coupons were applied on **'''+str(is_coupon_applied[True])+''' orders** 

> Coupon **'''+str(coupon_applied['Coupon Code'][0])+'''** was used **'''+str(coupon_applied['Order Count'][0])+'''** times

---

        '''),

    html.Div([
        html.Div([
            dcc.Graph(id='order_zone_series', figure=go.Figure([go.Pie(labels=list(order_zone_series.index), values=order_zone_series.tolist(), name='order_zone_series')], layout=go.Layout(title=go.layout.Title(text="Time Wise Order Breakdown"))))
        ], className="six columns"),

        html.Div([
            dcc.Graph(id='on_time', figure=go.Figure([go.Pie(labels=list(on_time_series.index), values=on_time_series.tolist(), name='on_time')], layout=go.Layout(title=go.layout.Title(text="On Time Delivery"))))
        ], className="six columns"),

    ], className="row", style={'margin-top': '20px'}),

    dcc.Markdown('''

> Most orders were placed during **'''+str(list(order_zone_series.index)[0])+'''**

> Out of **'''+str(total_orders)+''' orders**, **'''+ str(on_time_series[True])+''' orders** were delivered on time 

---
        '''),

    html.Div([

        html.Div([
            dcc.Graph(id='payment_method', figure=go.Figure([go.Bar(x=payment_method['Payment Method'].tolist(), y=payment_method['Order Count'].tolist())], layout=go.Layout(title=go.layout.Title(text="Payment Method"))))
        ], className="four columns"),

        html.Div([
            dcc.Graph(id='order_payment_method', figure=go.Figure([go.Bar(x=order_payment_method['Specific Payment Method'].tolist(), y=order_payment_method['Order Count'].tolist())], layout=go.Layout(title=go.layout.Title(text="Specific Payment Method"))))
        ], className="four columns"),

        html.Div([
            html.H6('Charges/Fee Breakdown'),
            dash_table.DataTable(id='fee_df',columns=[{"name": i, "id": i} for i in fee_df.columns],data=fee_df.to_dict('records'),style_cell={'textAlign': 'center'},)
        ], className="three columns"),

    ], className="row", style={'margin-top': '20px'}),



], style={'padding': '20px'})

if __name__ == '__main__':
    app.run_server(debug=True)