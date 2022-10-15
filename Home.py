import os
os.environ['NUMEXPR_MAX_THREADS'] = '16'
import datetime
import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import re


@st.cache
def GetMuch(x):
    pattern = re.compile(r'[A-Za-z]')
    m=re.findall(pattern,x)
    if m:
        return ''.join(set(m))

@st.cache
def get_data(option2, option3):
    #读取生产计划单并对应到班组
    work_plan = pd.read_csv('生产计划单.csv')
    work_plan = work_plan[['生产单号','物料编号','名称','规格','计划数量','预计开始时间','预计结束时间','工序','生产状态']]
    #pd.set_option('mode.chained_assignment', None)
    work_plan['组别'] = work_plan.apply(lambda x:GetMuch(x["工序"]) ,axis = 1)
    
    #读取生产看板
    work_act = pd.read_csv('生产看板.csv')
    work_act = work_act[['生产单号','物料编号','物料名称','规格','计划数量','末道工序-合格数','生产已入库']]

    #关联生产计划单和生产看板
    work_plan_data = pd.merge(work_plan,work_act.loc[:, ["生产单号",'末道工序-合格数','生产已入库']],how='left',on = '生产单号')

    #过滤班组和生产计划单状态
    if option3 == '全部':
        work_plan_data = work_plan_data[work_plan_data['组别'].str.contains(option2)]
    else:
        work_plan_data = work_plan_data[(work_plan_data['组别'].str.contains(option2))&(work_plan_data['生产状态']==option3)]
    work_plan_data['末道工序-合格数']=work_plan_data['末道工序-合格数'].fillna(0)
    work_plan_data['生产已入库']=work_plan_data['生产已入库'].fillna(0)
    return work_plan_data


def main():
    st.sidebar.subheader("蜀益机械生产计划概览")
    accounts = ['A组','B组','C组','D组','E组','J组','基础资料']
    account_selections = st.sidebar.selectbox(
        "选择查看类型", options=accounts
    )
    if account_selections in ['A组','B组','C组','D组','E组','J组']:
        st.header(" %s 生产计划执行概况"%account_selections)
        st.info('十一月份钉钉生产报工应用开放数据接口，上线后会将看板转换为自动同步模式！')

        col1, col2, col3 = st.columns(3)
        with col1:
            option = st.selectbox('选择查看模式',('进度图', '明细表格','文字版','生产概况绩效指标'))
        with col2:
            option2 = st.selectbox('选择查看状态',('全部','进行中', '已完成'))

        work_plan_all_data = get_data(account_selections.split('组')[0],option2)

        work_plan_data = work_plan_all_data.groupby('预计结束时间')
        if option == '进度图':
            for name,group in work_plan_data:
                st.subheader(name + '需要完成订单')
                col1, col2, col3 = st.columns(3)
                group.sort_values("末道工序-合格数",inplace = True, ascending=False) 
                group.reset_index()
                work_plan_group_data = group.reset_index()
                for index, row in work_plan_group_data.iterrows():
                    if index%3 == 0:
                        with col1:
                            st.info(row['名称']+'\n\n'+'计划数:'+ str(row['计划数量'])+'\n\n'+ '末道工序-合格数:'+str(int(row['末道工序-合格数'])))
                            st.progress(row['末道工序-合格数']/row['计划数量'] if row['末道工序-合格数']/row['计划数量'] <= 1 else 100)
                    elif index%3 == 1:
                        with col2:
                            st.info(row['名称']+'\n\n'+'计划数:'+ str(row['计划数量'])+'\n\n'+ '末道工序-合格数:'+str(int(row['末道工序-合格数'])))
                            st.progress(row['末道工序-合格数']/row['计划数量'] if row['末道工序-合格数']/row['计划数量'] <= 1 else 100)
                    else:
                        with col3:
                            st.info(row['名称']+'\n\n'+'计划数:'+ str(row['计划数量'])+'\n\n'+ '末道工序-合格数:'+str(int(row['末道工序-合格数'])))
                            st.progress(row['末道工序-合格数']/row['计划数量'] if row['末道工序-合格数']/row['计划数量'] <= 1 else 100)
        elif option == '明细表格':
            for name,group in work_plan_data:
                with st.expander(name):
                    AAA = pd.DataFrame(group)
                    AgGrid(AAA)
        elif option == '文字版':
            for name,group in work_plan_data:
                for index, row in group.iterrows():
                    st.error(name+'日需要完成@'+row['名称']+'@计划数:'+ str(row['计划数量'])+ '@末道工序-合格数:'+str(int(row['末道工序-合格数'])))
        else:
            st.write('----')
            today=datetime.date.today()
            yuqi = work_plan_all_data[work_plan_all_data['预计结束时间'] < str(today)]
            col1, col2, col3,col4 = st.columns(4)
            with col1:
                st.metric(
                    "总订单数",
                    f"{work_plan_all_data.shape[0]}",
                    20,
                )
            with col2:
                st.metric(
                    "待产订单数",
                    f"{yuqi.shape[0]}",
                    -20,
                )
            with col3:
                st.metric(
                    "逾期订单数",
                    f"{yuqi.shape[0]}",
                    -20,
                )
            with col4:
                if work_plan_all_data.shape[0] != 0:
                    xx = yuqi.shape[0]/work_plan_all_data.shape[0]
                else:
                    xx=0
                st.metric(
                    "逾期率",
                    f"{xx:.2%}",
                    -20,
                )
            st.write('----')
            result1 = pd.pivot_table(work_plan_all_data,index='预计结束时间' , values = ['生产单号'] , aggfunc='count')
            chart_data = pd.DataFrame(result1)
            st.bar_chart(chart_data,width = 500,height=500)

    elif account_selections == '基础资料':
        st.header("蜀益机械仓储看板概况")
        st.info('十一月份钉钉生产报工应用开放数据接口，上线后会将看板转换为自动同步模式！')
        uploaded_warehouse_file = st.file_uploader("请上传最新版仓储看板")
        if uploaded_warehouse_file is not None:
            uploaded_warehouse = pd.read_excel(uploaded_warehouse_file)
            uploaded_warehouse.to_csv("仓储看板.csv")
        uploaded_plan_file = st.file_uploader("请上传最新版生产计划单")
        if uploaded_plan_file is not None:
            uploaded_plan = pd.read_excel(uploaded_plan_file,header = 1)
            uploaded_plan.to_csv("生产计划单.csv")
        uploaded_baog_file = st.file_uploader("请上传最新版报工信息单")
        if uploaded_baog_file is not None:
            uploaded_baog_data = pd.read_excel(uploaded_baog_file, header=1, index_col=False)
            uploaded_baog_data.to_csv("报工单.csv",index=False)
        uploaded_paig_file = st.file_uploader("请上传最新版派工单")
        if uploaded_paig_file is not None:
            uploaded_paig_data = pd.read_excel(uploaded_paig_file, index_col=False)
            uploaded_paig_data.to_csv("派工单.csv",index=False)
        uploaded_makeban_file = st.file_uploader("请上传最新版生产看板")
        if uploaded_makeban_file is not None:
            uploaded_makeban_data = pd.read_excel(uploaded_makeban_file, index_col=False)
            uploaded_makeban_data.to_csv("生产看板.csv",index=False)
if __name__ == "__main__":
    st.set_page_config(
        "蜀益机械生产管理大屏",
        "📊",
        initial_sidebar_state="expanded",
        layout="wide",
    )
    main()
