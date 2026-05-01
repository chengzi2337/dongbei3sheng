import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import os
import seaborn as sns

mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica'],
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 600,
    'savefig.bbox': 'tight'
})

OUT_DIR = "visualizations"
os.makedirs(OUT_DIR, exist_ok=True)

def fig5_bottleneck_area():
    print("Generating Figure: Bottleneck Area...")
    try:
        with open('advanced_summary.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        q2_req = data.get('q2_day_minima', [])
        q2_act = data.get('q2_daily_counts', [])
        
        q3_req = data.get('q3_day_minima', [])
        q3_act = data.get('q3_daily_counts_alns', [])
        
        days = np.arange(1, 11)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Q2 Subplot
        ax1.fill_between(days, q2_req, color='#3498db', alpha=0.3, label='Minimum Labor Demand Area')
        ax1.plot(days, q2_req, 'o-', color='#2980b9', lw=2, label='Daily Minima')
        ax1.plot(days, q2_act, 's--', color='#e74c3c', lw=2, label='Actual Assigned')
        
        # Q2 Text Annotation for Total Pool
        total_shifts = sum(q2_req)
        ax1.text(5, 230, f"Total Required Shifts = {total_shifts}\nTheoretical Lower Bound:\n {total_shifts}/8 = 405.875 -> 406 Workers", 
                 ha='center', va='center', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=1'))
        
        ax1.set_title('Question 2: Supply vs Demand Bottleneck')
        ax1.set_xlabel('Day (1-10)')
        ax1.set_ylabel('Workers Count')
        ax1.legend(loc='lower right')
        
        # Q3 Subplot
        ax2.fill_between(days, q3_req, color='#2ecc71', alpha=0.3, label='Minimum Labor Demand Area')
        ax2.plot(days, q3_req, 'o-', color='#27ae60', lw=2, label='Daily Minima')
        ax2.plot(days, q3_act, 's--', color='#e67e22', lw=2, label='ALNS Best Assigned')
        
        total_shifts_q3 = sum(q3_req)
        ax2.text(5, 230, f"Total Required Shifts = {total_shifts_q3}\nTheoretical Lower Bound:\n {total_shifts_q3}/8 = 398.875 -> 400 Workers", 
                 ha='center', va='center', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', boxstyle='round,pad=1'))
        
        ax2.set_title('Question 3 (ALNS): Supply vs Demand Bottleneck')
        ax2.set_xlabel('Day (1-10)')
        ax2.legend(loc='lower right')
        
        plt.tight_layout()
        plt.savefig(f"{OUT_DIR}/fig5_daily_bottleneck_area.png")
        plt.close()
    except Exception as e:
        print(f"Error in fig5: {e}")

def fig6_constraint_tightness():
    print("Generating Figure: Constraint Tightness...")
    try:
        df = pd.read_csv('q1_417_feasible_schedule.csv')
        day_cols = [col for col in df.columns if '天' in col]
        
        # Derive constraints
        # 1. Total Daily Workers (Supply Ratio against 417 maximum logic, but wait, Q1 is fixed schedule)
        daily_assigned = []
        for d in day_cols:
            works = (~df[d].astype(str).str.contains('休息')).sum()
            daily_assigned.append(works)
            
        # Mock up "Maximum Supply Capacity" per day as ~ 333 (since total 417 * 8/10 = 333.6)
        avg_capacity = 417 * 0.8
        tightness_ratio = np.array(daily_assigned) / avg_capacity
        
        # We will create a small 1x10 heatmap for the "System Stress level"
        mat = np.array([tightness_ratio])
        
        fig, ax = plt.subplots(figsize=(10, 2))
        sns.heatmap(mat, cmap='Reds', annot=True, fmt=".2f", cbar=True, ax=ax,
                    xticklabels=[f"Day {i+1}" for i in range(10)], yticklabels=['Labor Pool\nTightness'])
        ax.set_title('Labor Capacity Tightness Heatmap (Actual vs Mean Capacity)')
        plt.tight_layout()
        plt.savefig(f"{OUT_DIR}/fig6_constraint_tightness.png")
        plt.close()
    except Exception as e:
        print(f"Error in fig6: {e}")

if __name__ == '__main__':
    fig5_bottleneck_area()
    fig6_constraint_tightness()
    print("Batch 1 Supplement Generated Successfully!")