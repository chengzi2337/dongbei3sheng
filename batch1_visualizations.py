import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib as mpl

# Academic Style Configuration
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

def fig1_waterfall():
    print("Generating Figure 1: Waterfall...")
    try:
        with open('q1_video_discrepancy_audit.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        lp = data.get('total_lp_relaxation', 411.375)
        ceil_lp = data.get('total_ceil_lp_bound', 415)
        int_workers = data.get('total_integer_workers', 417)
        
        fig, ax = plt.subplots(figsize=(8, 5))
        labels = ['LP Relaxation', 'Ceiling Adjustment', 'Integer Feasible Constraint', 'Final Feasible Bound']
        values = [lp, ceil_lp - lp, int_workers - ceil_lp, int_workers]
        starts = [0, lp, ceil_lp, 0]
        colors = ['#7f8c8d', '#e74c3c', '#e67e22', '#2980b9']
        
        ax.bar(labels, values, bottom=starts, color=colors, width=0.5, edgecolor='black', alpha=0.8)
        for i, (v, s) in enumerate(zip(values, starts)):
            ax.text(i, s + v/2 if starts[i] > 0 else v + 1, f"{v:.3f}" if i==1 else str(int(v)), 
                    ha='center', va='center' if starts[i]>0 else 'bottom', fontweight='bold', color='white' if starts[i]>0 else 'black')
        
        ax.plot([0, 1, 2, 3], [lp, ceil_lp, int_workers, int_workers], 'k--', alpha=0.5)
        ax.set_ylabel('Required Workers')
        ax.set_title('Lower Bound Audit Waterfall (Q1)')
        plt.tight_layout()
        plt.savefig(f"{OUT_DIR}/fig1_lb_audit_waterfall.png")
        plt.close()
    except Exception as e:
        print(f"Error in fig1: {e}")

def fig2_dumbbell():
    print("Generating Figure 2: Dumbbell...")
    try:
        fig, ax = plt.subplots(figsize=(8, 4))
        # Data
        labels = ['Problem 1', 'Problem 2', 'Problem 3']
        lbs = [411.375, 406, 400]
        ceil_lbs = [415, 406, 400]
        feasibles = [417, 406, 400]
        
        for i, (lb, clb, feas) in enumerate(zip(lbs, ceil_lbs, feasibles)):
            # Line connecting
            ax.plot([lb, feas], [i, i], color='#95a5a6', zorder=1, lw=2)
            # Scatter points
            ax.scatter([lb], [i], color='#7f8c8d', s=100, zorder=2, label='LP Bound' if i==0 else "")
            ax.scatter([clb], [i], color='#e67e22', s=100, zorder=3, label='Ceil Bound' if i==0 else "")
            ax.scatter([feas], [i], color='#2980b9', s=150, zorder=4, label='Feasible (ALNS/MIP)' if i==0 else "")
            
            ax.text(lb, i + 0.15, f"{lb:.1f}", ha='center', fontsize=9, color='#7f8c8d')
            if feas != lb and feas != clb:
                ax.text(clb, i - 0.15, f"{clb}", ha='center', fontsize=9, color='#e67e22')
            if feas != lb:
                ax.text(feas, i + 0.15, f"{feas}", ha='center', fontsize=9, fontweight='bold', color='#2980b9')
            if lb == feas:
                ax.text(feas, i + 0.15, f"Optimality Gap=0.00%", ha='center', fontsize=10, fontweight='bold', color='green')
            elif i == 0:
                ax.text(feas+2, i, f"Gap: 417-415=2", va='center', fontsize=10, fontweight='bold', color='red')
                
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        ax.set_xlabel('Total Required Workers')
        ax.set_title('Lower Bound vs Feasible Solution (Optimality Gap)')
        ax.legend(loc='lower right')
        plt.tight_layout()
        plt.savefig(f"{OUT_DIR}/fig2_lb_vs_feasible_dumbbell.png")
        plt.close()
    except Exception as e:
        print(f"Error in fig2: {e}")

def fig3_heatmap():
    print("Generating Figure 3: Heatmap...")
    try:
        df = pd.read_csv('q1_417_feasible_schedule.csv')
        day_cols = [col for col in df.columns if '天' in col]
        # binary matrix: 0 for 休息, 1 for work
        mat = []
        for _, row in df.iterrows():
            worker_sched = [0 if '休息' in str(row[d]) else 1 for d in day_cols]
            mat.append(worker_sched)
            
        mat = np.array(mat)
        # Sort by total days worked descending, then by first day worked
        days_worked = mat.sum(axis=1)
        first_day = np.argmax(mat > 0, axis=1)
        sorted_idx = np.lexsort((days_worked, -first_day))[::-1]
        sorted_mat = mat[sorted_idx]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        cmap = sns.color_palette(["#ecf0f1", "#2c3e50"])
        sns.heatmap(sorted_mat, cmap=cmap, cbar=False, ax=ax, xticklabels=[f"Day{i+1}" for i in range(10)])
        ax.set_ylabel('Workers (417 sorted)')
        ax.set_title('Macro Schedule Matrix Waterfall (Q1: 417 x 10)')
        ax.set_yticks([0, 100, 200, 300, 417])
        plt.tight_layout()
        plt.savefig(f"{OUT_DIR}/fig3_q1_schedule_heatmap.png")
        plt.close()
    except Exception as e:
        print(f"Error in fig3: {e}")

def fig4_convergence():
    print("Generating Figure 5: ALNS Convergence...")
    try:
        df = pd.read_csv('q3_alns_convergence.csv')
        fig, ax1 = plt.subplots(figsize=(10, 5))
        
        # Plot candidate scores as density cloud
        ax1.scatter(df['iteration'], df['candidate_score'], color='#3498db', alpha=0.1, s=10, label='Candidate Cloud', zorder=1)
        # Plot best score
        ax1.plot(df['iteration'], df['best_score'], color='#e74c3c', lw=2, label='Best Score', zorder=2)
        
        ax1.set_xlabel('Iteration')
        ax1.set_ylabel('Score / Objective Value', color='#2c3e50')
        ax1.set_title('ALNS Search Trajectory and Density Cloud (Q3)')
        
        # Temperature on second axis
        ax2 = ax1.twinx()
        ax2.plot(df['iteration'], df['temperature'], color='#f39c12', lw=2, alpha=0.7, label='Temperature')
        ax2.set_ylabel('Temperature', color='#f39c12')
        
        # Legends
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines + lines2, labels + labels2, loc='upper right')
        
        plt.tight_layout()
        plt.savefig(f"{OUT_DIR}/fig5_alns_convergence.png")
        plt.close()
    except Exception as e:
        print(f"Error in fig4: {e}")

if __name__ == '__main__':
    fig1_waterfall()
    fig2_dumbbell()
    fig3_heatmap()
    fig4_convergence()
    print("Batch 1 Visualizations Generated Successfully!")
