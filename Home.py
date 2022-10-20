import os
os.environ['NUMEXPR_MAX_THREADS'] = '16'
import datetime
import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import re

pub_sheet_url = 'https://docs.google.com/spreadsheets/d/1z2lMhtNqcnBQklOVeldK0fjBdfMlm4-Gn8PQ5GoX0zU/edit?usp=sharing'

@st.cache
def GetMuch(x):
    pattern = re.compile(r'[A-Za-z]')
    m=re.findall(pattern,x)
    if m:
        return ''.join(set(m))

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
        baogong_data = pd.read_csv('派工单.csv')
        baogong_data = baogong_data[['计划单号','工序','派工数量','派工人','报工人','报工合格数（含审批中）']]
        baogong_data.rename(columns={'计划单号':'生产单号'}, inplace = True)
        
        if option == '进度图':
            
            
            for name,group in work_plan_data:
                st.subheader(name + '需要完成订单')
                group.sort_values("末道工序-合格数",inplace = True, ascending=False) 
                group.reset_index()
                work_plan_group_data = group.reset_index()
                #st.write(work_plan_group_data)
                col1, col2 = st.columns(2)
                work_plan_group_data4 = work_plan_group_data.copy()
                work_plan_group_data2 = work_plan_group_data4['工序'].str.split(',', expand=True)
                work_plan_group_data2 = work_plan_group_data2.stack()
                
                work_plan_group_data2 = work_plan_group_data2.reset_index(level=1, drop=True).rename('工序')
                #st.write(work_plan_group_data2)  
                work_plan_group_data_new = work_plan_group_data.drop(['工序'], axis=1).join(work_plan_group_data2)


                xxx = pd.merge(work_plan_group_data_new, baogong_data.loc[:, ["生产单号",'工序','派工数量','派工人','报工人','报工合格数（含审批中）']], how='left',on = ['生产单号','工序'])
                #st.write(xxx.info())
                xxx = xxx[xxx['工序'].str.contains(account_selections2)]
                xxx[['末道工序-合格数','报工合格数（含审批中）','派工数量']]=xxx[['末道工序-合格数','报工合格数（含审批中）','派工数量']].fillna(0)
                xxx['派工人']=xxx['派工人'].fillna('未派工')
                xxx['报工人']=xxx['报工人'].fillna('未报工')
                xxx[['末道工序-合格数','报工合格数（含审批中）','派工数量']]=xxx[['末道工序-合格数','报工合格数（含审批中）','派工数量']].astype('int64')
                xxx2 = xxx.groupby(['生产单号','名称', '末道工序-合格数','计划数量'])
                aaa = 0
                col1, col2, col3 = st.columns(3)
                for name, group222 in xxx2:
                    group222.reset_index()
                    #st.write(aaa)
                    if aaa%3 == 0:
                        with col1:
                            #st.write(group222.index)
                            st.info(name[1]+'\n\n'+ '[' +'计划数:'+ str(name[3])+']'+ '['+ '末道工序-合格数:'+str(name[2])+']')
                            aa = ''
                            for index, row in group222.iterrows():
                                if str(row['派工人']) == '未派工':
                                    aa = aa + '[' + row['工序']+ ']'  + '[' + str(row['派工人'])  + ']'+ '[' + str(row['报工人'])  + ']'+ '\n\n' 
                                else:
                                    #aa.append([row['工序']+'派工数:'+ str(row['派工数量']) + '报工数:' + str(row['报工合格数（含审批中）']) +'\n\n'])
                                    aa = aa + '[' + row['工序']+ ']'  + '[' + str(row['派工人'])  + '派'  + str(row['派工数量']) + ']'  + '[' + str(row['报工人']) +  '报' + str(row['报工合格数（含审批中）']) + ']'+ '\n\n' 
                        #with col2:
                            #for i in aa:
                            st.text_area(str(name[0]),aa,label_visibility='collapsed',height=100)
                            aaaa = group222[group222['派工人']=='未派工']
                            bbbb = group222[group222['报工合格数（含审批中）']==0]
                            st.progress(1-aaaa.shape[0]/group222.shape[0])
                            st.progress(1-bbbb.shape[0]/group222.shape[0])
                    if aaa%3 == 1:
                        with col2:
                            #st.write('<font color=>THIS TEXT WILL BE RED</font>')
                            #st.write(group222.index)
                            st.info(name[1]+'\n\n'+ '[' +'计划数:'+ str(name[3])+']'+ '['+ '末道工序-合格数:'+str(name[2])+']')
                            aa = ''
                            for index, row in group222.iterrows():
                                if str(row['派工人']) == '未派工':
                                    aa = aa + '[' + row['工序']+ ']'  + '[' + str(row['派工人'])  + ']'+ '[' + str(row['报工人'])  + ']'+ '\n\n' 
                                else:
                                    #aa.append([row['工序']+'派工数:'+ str(row['派工数量']) + '报工数:' + str(row['报工合格数（含审批中）']) +'\n\n'])
                                    aa = aa + '[' + row['工序']+ ']'  + '[' + str(row['派工人'])  + '派'  + str(row['派工数量']) + ']'  + '[' + str(row['报工人']) +  '报' + str(row['报工合格数（含审批中）']) + ']'+ '\n\n' 
                        #with col2:
                            #for i in aa:
                            st.text_area(str(name[0]),aa,label_visibility='collapsed',height=100)
                            aaaa = group222[group222['派工人']=='未派工']
                            bbbb = group222[group222['报工合格数（含审批中）']==0]
                            st.progress(1-aaaa.shape[0]/group222.shape[0])
                            st.progress(1-bbbb.shape[0]/group222.shape[0])
                    if aaa%3 == 2:
                        with col3:
                            #st.write(group222.index)
                            st.info(name[1]+'\n\n'+ '[' +'计划数:'+ str(name[3])+']'+ '['+ '末道工序-合格数:'+str(name[2])+']')
                            aa = ''
                            for index, row in group222.iterrows():
                                if str(row['派工人']) == '未派工':
                                    aa = aa + '[' + row['工序']+ ']'  + '[' + str(row['派工人'])  + ']'+ '[' + str(row['报工人'])  + ']'+ '\n\n' 
                                else:
                                    #aa.append([row['工序']+'派工数:'+ str(row['派工数量']) + '报工数:' + str(row['报工合格数（含审批中）']) +'\n\n'])
                                    aa = aa + '[' + row['工序']+ ']'  + '[' + str(row['派工人'])  + '派'  + str(row['派工数量']) + ']'  + '[' + str(row['报工人']) +  '报' + str(row['报工合格数（含审批中）']) + ']'+ '\n\n' 
                        #with col2:
                            #for i in aa:
                            st.text_area(str(name[0]),aa,label_visibility='collapsed',height=100)
                            #st.write(group222)
                            aaaa = group222[group222['派工人']=='未派工']
                            bbbb = group222[group222['报工合格数（含审批中）']==0]
                            st.progress(1-aaaa.shape[0]/group222.shape[0])
                            st.progress(1-bbbb.shape[0]/group222.shape[0])
                    aaa = aaa + 1
                #with containss:
                    #for index, row in work_plan_group_data.iterrows():
                        #with col1:
                            #st.write('pl')
                            #st.write(row['名称']+'\n\n'+'计划数:'+ str(row['计划数量'])+'\n\n'+ '末道工序-合格数:'+str(int(row['末道工序-合格数'])))
                            #st.progress(row['末道工序-合格数']/row['计划数量'] if row['末道工序-合格数']/row['计划数量'] <= 1 else 100)
                        #with col2:
                            #for name,group in xxx2:
                            #st.write(name)
                                #st.text(group[['工序','派工数量','派工人','报工人','报工合格数（含审批中）']])

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
            uploaded_warehouse = pd.DataFrame(uploaded_warehouse)
            open('仓储看板.csv', 'w',encoding='utf-8').write(uploaded_warehouse.to_csv())
        uploaded_plan_file = st.file_uploader("请上传最新版生产计划单")
        if uploaded_plan_file is not None:
            uploaded_plan = pd.read_excel(uploaded_plan_file,header = 1)
            uploaded_plan = pd.DataFrame(uploaded_plan)
            with open('生产计划单.csv', 'w',encoding='utf-8') as f:
                f.truncate()
                f.write(uploaded_plan.to_csv())
        uploaded_baog_file = st.file_uploader("请上传最新版报工信息单")
        if uploaded_baog_file is not None:
            uploaded_baog_data = pd.read_excel(uploaded_baog_file, header=1, index_col=False)
            uploaded_baog_data = pd.DataFrame(uploaded_baog_data)
            open('报工.csv', 'w',encoding='utf-8').write(uploaded_baog_data.to_csv())
        uploaded_paig_file = st.file_uploader("请上传最新版派工单")
        if uploaded_paig_file is not None:
            uploaded_paig_data = pd.read_excel(uploaded_paig_file, index_col=False)
            uploaded_paig_data = pd.DataFrame(uploaded_paig_data)
            open('派工单.csv', 'w',encoding='utf-8').write(uploaded_paig_data.to_csv())
        uploaded_makeban_file = st.file_uploader("请上传最新版生产看板")
        if uploaded_makeban_file is not None:
            uploaded_makeban_data = pd.read_excel(uploaded_makeban_file, index_col=False)
            uploaded_makeban_data = pd.DataFrame(uploaded_makeban_data)
            with open('生产看板.csv', 'w',encoding='utf-8') as f:
                f.truncate()
                f.write(uploaded_makeban_data.to_csv())


if __name__ == "__main__":
    st.set_page_config(
        "蜀益机械生产管理大屏",
        "📊",
        initial_sidebar_state="expanded",
        layout="wide",
    )
    main()
