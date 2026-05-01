import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib as mpl
import warnings
warnings.filterwarnings('ignore')

mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'Microsoft YaHei', 'SimHei'],
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

def fig7_operator_evolution():
    print("Generating Figure 7: Operator Evolution Stacked Area...")
    try:
        df = pd.read_csv('q3_alns_convergence.csv')
        if 'destroy' not in df.columns or len(df) < 10:
            print("Not enough data for operator evolution.")
            return

        # Create bins for iterations to smooth the frequencies
        num_bins = min(20, len(df) // 5)
        df['iter_bin'] = pd.cut(df['iteration'], bins=num_bins)
        
        # Calculate frequency of destroy operators per bin
        crosstab = pd.crosstab(df['iter_bin'], df['destroy'], normalize='index')
        crosstab.index = [f"Phase {i+1}" for i in range(len(crosstab))]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        crosstab.plot.area(ax=ax, cmap='viridis', alpha=0.8, linewidth=0)
        ax.set_title('ALNS Operator Usage Frequency Evolution (Destroy Phase)')
        ax.set_xlabel('Search Phase')
        ax.set_ylabel('Operator Selection Probability')
        ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1))
        
        plt.tight_layout()
        plt.savefig(f"{OUT_DIR}/fig7_operator_evolution.png")
        plt.close()
    except Exception as e:
        print(f"Error in fig7: {e}")

def fig8_workload_raincloud():
    print("Generating Figure 8: Workload Raincloud / Violin Plot...")
    try:
        df = pd.read_csv('q1_417_feasible_schedule.csv')
        day_cols = [col for col in df.columns if '天' in col]
        
        work_days = []
        for _, row in df.iterrows():
            days_worked = sum([0 if '休息' in str(row[d]) else 1 for d in day_cols])
            work_days.append(days_worked)
            
        fig, ax = plt.subplots(figsize=(8, 4))
        
        # Raincloud-like composition
        sns.violinplot(x=work_days, color="#3498db", inner=None, alpha=0.4, ax=ax)
        sns.boxplot(x=work_days, color="white", width=0.1, boxprops={'zorder': 2}, ax=ax)
        sns.stripplot(x=work_days, color="#2980b9", alpha=0.5, jitter=True, zorder=1, size=4, ax=ax)
        
        ax.set_title('Workload Fairness Distribution (Days Worked per Person)')
        ax.set_xlabel('Total Working Days in 10-day period')
        ax.set_yticks([])
        
        # Statistical summary
        mean_val = np.mean(work_days)
        std_val = np.std(work_days)
        ax.text(0.05, 0.85, f"Mean: {mean_val:.2f} days\nStd Dev: {std_val:.2f}\nTotal Workers: 417", 
                transform=ax.transAxes, bbox=dict(facecolor='white', alpha=0.8, edgecolor='#bdc3c7'))
        
        plt.tight_layout()
        plt.savefig(f"{OUT_DIR}/fig8_workload_raincloud.png")
        plt.close()
    except Exception as e:
        print(f"Error in fig8: {e}")

def fig9_shift_transition():
    print("Generating Figure 9: Shift Transition Heatmap...")
    try:
        df = pd.read_csv('q1_417_feasible_schedule.csv')
        day_cols = [col for col in df.columns if '天' in col]
        
        transitions = {'Rest->Rest': 0, 'Rest->Work': 0, 'Work->Rest': 0, 'Work->Work': 0}
        
        for _, row in df.iterrows():
            for i in range(len(day_cols)-1):
                curr = 'Rest' if '休息' in str(row[day_cols[i]]) else 'Work'
                nxt = 'Rest' if '休息' in str(row[day_cols[i+1]]) else 'Work'
                transitions[f"{curr}->{nxt}"] += 1
                
        # Create matrix
        mat = np.array([
            [transitions['Work->Work'], transitions['Work->Rest']],
            [transitions['Rest->Work'], transitions['Rest->Rest']]
        ])
        
        fig, ax = plt.subplots(figsize=(6, 5))
        sns.heatmap(mat, annot=True, fmt="d", cmap="YlOrBr", 
                    xticklabels=['To Work', 'To Rest'], yticklabels=['From Work', 'From Rest'])
        ax.set_title('Shift State Transition Heatmap')
        plt.tight_layout()
        plt.savefig(f"{OUT_DIR}/fig9_shift_transition.png")
        plt.close()
    except Exception as e:
        print(f"Error in fig9: {e}")

def fig10_alns_phase_space():
    print("Generating Figure 10: ALNS Phase Space Scatter...")
    try:
        df = pd.read_csv('q3_alns_convergence.csv')
        df['score_diff'] = df['candidate_score'] - df['best_score']
        
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Scatter plot colored by 'accepted' status if possible or destroy operator
        if 'accepted' in df.columns and df['accepted'].nunique() > 1:
            scatter = ax.scatter(df['removed'], df['score_diff'], c=df['accepted'], 
                                 cmap='coolwarm', alpha=0.6, edgecolors='none', s=20)
            plt.colorbar(scatter, label='Accepted (1=Yes, 0=No)')
        else:
            scatter = ax.scatter(df['removed'], df['score_diff'], c=df['iteration'], 
                                 cmap='viridis', alpha=0.6, edgecolors='none', s=20)
            plt.colorbar(scatter, label='Iteration Phase')
            
        ax.axhline(0, color='red', linestyle='--', alpha=0.5, label='Global Best Level')
        ax.set_title('ALNS Phase Space (Destroy Size vs Yield)')
        ax.set_xlabel('Number of Items Removed (Destroy Magnitude)')
        ax.set_ylabel('Score Difference (Candidate - Best)')
        ax.set_yscale('symlog')  # Score differences can be huge
        
        plt.tight_layout()
        plt.savefig(f"{OUT_DIR}/fig10_alns_phase_space.png")
        plt.close()
    except Exception as e:
        print(f"Error in fig10: {e}")

if __name__ == '__main__':
    fig7_operator_evolution()
    fig8_workload_raincloud()
    fig9_shift_transition()
    fig10_alns_phase_space()
    print("Batch 2 Enhancements Generated Successfully!")