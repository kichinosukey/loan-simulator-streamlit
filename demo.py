from datetime import datetime as dt

import pandas as pd

import streamlit as st
import altair as alt

from lib import Payment, Income, Expence, Result


def plot_payment_view(data, color_payment_raw="blue", color_payment_net="blue", color_interest="red", opacity=0.5):

    plot_payment_raw = alt.Chart(data).mark_area(color=color_payment_raw, opacity=opacity).encode(
        x="date:T",
        y=alt.Y("payment:Q"),
        tooltip=["date", "payment"],
    )

    plot_payment_net = alt.Chart(data).mark_area(color=color_payment_net, opacity=opacity).encode(
        x="date:T",
        y=alt.Y("payment_net:Q"),
        tooltip=["date", "payment_net"],
    )

    plot_interest = alt.Chart(data).mark_area(color=color_interest, opacity=opacity).encode(
        x="date:T",
        y=alt.Y("interest:Q"),
        tooltip=["date", "interest"],
    )

    st.write(plot_payment_raw + plot_payment_net + plot_interest)



if __name__ == "__main__":
    
    # 初期設定
    st.markdown('## ローン設定')
    rate = st.number_input("年利[%]", min_value=0.100, max_value=5.000, value=1.00, step=0.01, key="rate")
    rate /= 100.0
    year_loan = st.number_input("借用期間[年]", min_value=1, max_value=35, value=30, step=1, key="year_loan")
    loan_principal = st.number_input("借入金額[万円]", min_value=1000, max_value=5000, value=3000, step=1, key="loan_principal")
    loan_principal_bonus = st.number_input("ボーナス返済分[万円]", min_value=0, max_value=int(loan_principal/2), value=0, step=1, key="loan_principal")
    loan_principal *= 10000
    loan_principal_bonus *= 10000
    loan_principal -= loan_principal_bonus
    months = st.number_input("支払い回数/年", min_value=1, max_value=12, value=12, step=1, key="month")
    pmt = Payment(rate, 
        year_loan=year_loan, 
        loan_principal=loan_principal-loan_principal_bonus, 
        months=months, start=None)

    # 毎月給与
    st.markdown('## 給与設定')
    income_raw = st.number_input("額面給与", min_value=100000, max_value=1000000, value=500000, step=10000, key="income_raw")
    deduction = st.number_input("控除", min_value=0, max_value=int(income_raw*0.5), value=int(income_raw*0.25), step=1000, key="deduction")
    save = st.number_input("積立", min_value=0, max_value=int(income_raw*0.5), value=int(income_raw*0.1), step=1000, key="save")
    income = Income(income_raw, deduction, save, start=None, periods=months*year_loan)

    # 賞与
    st.markdown('## ボーナス設定')
    income_raw_bonus = st.number_input("額面ボーナス", min_value=100000, max_value=1000000, value=500000, step=10000, key="income_raw_bonus")
    deduction_bonus = st.number_input("控除", min_value=0, max_value=int(income_raw*0.5), value=int(income_raw*0.25), step=1000, key="deduction_bonus")
    save_bonus = st.number_input("積立", min_value=0, max_value=int(income_raw*0.5), value=int(income_raw*0.1), step=1000, key="save_bonus")
    months_bonus_pmt = st.number_input("ボーナス支払い回数/年", min_value=0, max_value=2, value=2, step=1, key="month_bonus")
    month_now = int(dt.now().strftime('%m'))
    month_bonus_start = st.number_input("ボーナス支払い開始月", min_value=month_now, max_value=12, value=month_now, step=1, key="month_bonus_start")
    income_bonus = Income(income_raw_bonus, deduction_bonus, save_bonus, start=dt.now().strftime('%Y-')+str(month_bonus_start), freq='6M', periods=months_bonus_pmt*year_loan)

    # ボーナス返済
    if loan_principal_bonus > 0:
        pmt_bonus = Payment(rate, 
            year_loan=year_loan, 
            loan_principal=loan_principal_bonus, 
            months=months_bonus_pmt, start=dt.now().strftime('%Y-')+str(month_bonus_start), freq='6M')
    else:
        pmt_bonus = None
    
    # 支出設定
    st.markdown('## 支出設定')
    expence_monthly = st.number_input("毎月支出額", min_value=0, max_value=1000000, value=100000, step=1000, key="expence_monthly")
    expence_monthly *= -1
    expence = Expence(expence=expence_monthly, periods=months*year_loan)

    # 毎月収支、積立推移
    st.markdown('## 毎月収支')
    result = Result(pmt, income, expence, pmt_bonus, income_bonus)
    opacity = 0.5
    plot_total = alt.Chart(result.data).mark_area(color="green", opacity=opacity).encode(
        x=alt.X("%s:T" % result.col_date),
        y=alt.Y("%s:Q" % result.col_save_cumsum),
        tooltip=[result.col_date, result.col_save_cumsum, result.col_total]
    )
    st.write(plot_total)

    # 毎月返済額、利子
    st.markdown('## ローン支払額内訳')
    result = Result(pmt, income)
    plot_payment_view(result.data)
    if loan_principal_bonus > 0:
        result = Result(pmt_bonus, income_bonus)
        plot_payment_view(result.data)