from datetime import datetime as dt

import numpy as np
import numpy_financial as npf
import pandas as pd


class Core:

    def __init__(self, start, freq='M', periods=12):
        if start is None or not isinstance(start, str):
            start = dt.now().strftime('%Y-%m')
        self.idx_datetime = pd.date_range(start=start, freq=freq, periods=periods)

class Payment(Core):

    def __init__(self, rate_year, year_loan, loan_principal, start=None, months=12, freq='M'):
        super().__init__(start=start, freq=freq, periods=year_loan*months)
        self.col_pmt = 'payment'
        self.col_pmt_net = 'payment_net'
        self.col_int = 'interest'
        self.rate_year = rate_year
        self.months = months
        self.rate_month = rate_year / self.months 
        self.nper = year_loan * self.months
        self.loan_principal = loan_principal
        self.pmt = npf.pmt(self.rate_month, self.nper, self.loan_principal)
        self.ipmt = npf.ipmt(self.rate_month, np.arange(self.nper)+1, self.nper, self.loan_principal)
        self.data = pd.DataFrame({self.col_int:self.ipmt}, index=self.idx_datetime)
        self.data[self.col_pmt] = self.pmt
        self.data[self.col_pmt_net] = self.data[self.col_pmt] - self.data[self.col_int]


class Income(Core):

    def __init__(self, income_raw, deduction, save, start=None, periods=12, freq='M'):
        super().__init__(start=start, freq=freq, periods=periods)
        self.col_inc_raw = 'income_raw'
        self.col_inc_net = 'income_net'
        self.col_ded = 'deduction'
        self.col_save = 'save'
        self.income_raw = income_raw
        self.deduction = deduction
        self.save = save
        self.income_net = income_raw - deduction - save
        self.data = pd.DataFrame({
                self.col_inc_raw:np.ones(len(self.idx_datetime))*self.income_raw,
                self.col_inc_net:np.ones(len(self.idx_datetime))*self.income_net,
                self.col_ded:np.ones(len(self.idx_datetime))*self.deduction,
                self.col_save:np.ones(len(self.idx_datetime))*self.save}, index=self.idx_datetime)


class Expence(Core):

    def __init__(self, expence=0, start=None, freq='M', periods=12):
        super().__init__(start=start, freq=freq, periods=periods)
        self.col_exp = 'expence_net'
        self.expence = expence
        self.data = pd.DataFrame({
               self.col_exp:np.ones(len(self.idx_datetime))*self.expence}, index=self.idx_datetime)        


class Result:

    def __init__(self, pmt_monthly, income_monthly, expence_monthly=None, pmt_bonus=None, income_bonus=None):
        self.col_date = 'date'
        self.col_total = 'pmt_and_income'
        self.col_save_cumsum = 'save_cumsum'
        self.col_int = pmt_monthly.col_int
        self.col_pmt = pmt_monthly.col_pmt
        self.col_pmt_net = pmt_monthly.col_pmt_net
        self.col_inc_net = income_monthly.col_inc_net
        self.col_save = income_monthly.col_save
        self.idx_datetime = pmt_monthly.idx_datetime

        self.data = pd.DataFrame({
            self.col_int:pmt_monthly.data[self.col_int].values,
            self.col_pmt:pmt_monthly.data[self.col_pmt].values,
            self.col_pmt_net:pmt_monthly.data[self.col_pmt_net].values,
            self.col_inc_net:income_monthly.data[self.col_inc_net].values,
            self.col_save:income_monthly.data[self.col_save].values
            }, index=self.idx_datetime)

        self.data_bonus = pd.DataFrame({'dummy': np.zeros(len(self.idx_datetime))}, index=self.idx_datetime)
        if pmt_bonus is not None:
            self.data_bonus = pd.merge(self.data_bonus, pmt_bonus.data, left_index=True, right_index=True, how='outer')
            self.data_bonus.fillna(0, inplace=True)
            self.data[self.col_pmt] += self.data_bonus[self.col_pmt].values
            self.data[self.col_int] += self.data_bonus[self.col_int].values

        if income_bonus is not None:
            self.data_bonus = pd.merge(self.data_bonus, income_bonus.data, left_index=True, right_index=True, how='outer')
            self.data_bonus.fillna(0, inplace=True)
            assert self.data.shape[0] == self.data_bonus.shape[0]
            self.data[self.col_inc_net] += self.data_bonus[self.col_inc_net].values
            self.data[self.col_save] += self.data_bonus[self.col_save].values
        
        self.data[self.col_total] = self.data[self.col_inc_net] + self.data[self.col_pmt]
        if expence_monthly is not None:
           self.col_exp = expence_monthly.col_exp
           self.data[self.col_exp] = expence_monthly.data[self.col_exp].values
           self.data[self.col_total] += self.data[self.col_exp]
        self.data[self.col_save_cumsum] = self.data[self.col_total].cumsum() + self.data[self.col_save].cumsum()

        self.data.reset_index(inplace=True)
        self.data = self.data.rename(columns={'index': self.col_date})
        self.data.fillna(0, inplace=True)