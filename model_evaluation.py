"""
Model Evaluation Module for Carbon Tracker
============================================
Comprehensive evaluation metrics with visualizations:
- Accuracy, Precision, Recall, F1 Score
- Confusion Matrix
- ROC Curve with AUC
- Classification Report
- Feature Importance (if applicable)

Author: Carbon Tracker Team
Date: 2026-05-13
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_curve, auc, roc_auc_score,
    classification_report, precision_recall_curve,
    matthews_corrcoef, cohen_kappa_score
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Set style for better visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


class ModelEvaluator:
    """
    Comprehensive model evaluation class for classification tasks.
    Generates all key metrics and visualizations.
    """
    
    def __init__(self, y_true, y_pred, y_pred_proba=None, model_name="Model"):
        """
        Initialize evaluator with predictions
        
        Args:
            y_true: Actual labels
            y_pred: Predicted labels (binary 0/1)
            y_pred_proba: Prediction probabilities (optional, for ROC curve)
            model_name: Name of the model for reporting
        """
        self.y_true = np.array(y_true)
        self.y_pred = np.array(y_pred)
        self.y_pred_proba = np.array(y_pred_proba) if y_pred_proba is not None else None
        self.model_name = model_name
        self.metrics = {}
        
    def calculate_metrics(self):
        """Calculate all evaluation metrics"""
        self.metrics = {
            'Accuracy': accuracy_score(self.y_true, self.y_pred),
            'Precision': precision_score(self.y_true, self.y_pred, zero_division=0),
            'Recall': recall_score(self.y_true, self.y_pred, zero_division=0),
            'F1 Score': f1_score(self.y_true, self.y_pred, zero_division=0),
            'Matthews CC': matthews_corrcoef(self.y_true, self.y_pred),
            "Cohen's Kappa": cohen_kappa_score(self.y_true, self.y_pred),
        }
        
        # Add AUC if probabilities are available
        if self.y_pred_proba is not None:
            self.metrics['AUC-ROC'] = roc_auc_score(self.y_true, self.y_pred_proba)
        
        return self.metrics
    
    def print_metrics_report(self):
        """Print formatted metrics report"""
        print("\n" + "="*70)
        print(f"MODEL EVALUATION REPORT: {self.model_name}")
        print("="*70)
        
        self.calculate_metrics()
        
        print("\n📊 PRIMARY METRICS:")
        print(f"  Accuracy:      {self.metrics['Accuracy']:.4f} ({self.metrics['Accuracy']*100:.2f}%)")
        print(f"  Precision:     {self.metrics['Precision']:.4f}")
        print(f"  Recall:        {self.metrics['Recall']:.4f}")
        print(f"  F1 Score:      {self.metrics['F1 Score']:.4f}")
        
        print("\n📈 ADVANCED METRICS:")
        print(f"  Matthews CC:   {self.metrics['Matthews CC']:.4f}")
        cohen_kappa = self.metrics["Cohen's Kappa"]
        print(f"  Cohen's Kappa: {cohen_kappa:.4f}")
        if 'AUC-ROC' in self.metrics:
            print(f"  AUC-ROC:       {self.metrics['AUC-ROC']:.4f}")
        
        print("\n" + "-"*70)
        print("CLASSIFICATION REPORT:")
        print("-"*70)
        print(classification_report(self.y_true, self.y_pred, 
                                   target_names=['Negative', 'Positive']))
        print("="*70 + "\n")
    
    def plot_confusion_matrix(self, save_path=None):
        """Plot and save confusion matrix"""
        cm = confusion_matrix(self.y_true, self.y_pred)
        
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=['Negative', 'Positive'],
                   yticklabels=['Negative', 'Positive'],
                   cbar_kws={'label': 'Count'},
                   ax=ax, annot_kws={'size': 14})
        
        ax.set_title(f'Confusion Matrix - {self.model_name}', fontsize=14, fontweight='bold')
        ax.set_ylabel('True Label', fontsize=12)
        ax.set_xlabel('Predicted Label', fontsize=12)
        
        # Add counts info
        tn, fp, fn, tp = cm.ravel()
        textstr = f'TN: {tn} | FP: {fp}\nFN: {fn} | TP: {tp}'
        ax.text(1.5, -0.3, textstr, fontsize=10, ha='center',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ Confusion Matrix saved to: {save_path}")
        
        plt.show()
        return cm
    
    def plot_roc_curve(self, save_path=None):
        """Plot and save ROC curve"""
        if self.y_pred_proba is None:
            print("⚠️  Probability predictions required for ROC curve!")
            return None
        
        # Handle both binary and multi-class probability formats
        if len(self.y_pred_proba.shape) > 1 and self.y_pred_proba.shape[1] > 1:
            proba = self.y_pred_proba[:, 1]
        else:
            proba = self.y_pred_proba
        
        fpr, tpr, thresholds = roc_curve(self.y_true, proba)
        roc_auc = auc(fpr, tpr)
        
        fig, ax = plt.subplots(figsize=(9, 7))
        
        # Plot ROC curve
        ax.plot(fpr, tpr, color='darkorange', lw=3, label=f'ROC curve (AUC = {roc_auc:.4f})')
        ax.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random Classifier')
        
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('False Positive Rate (1 - Specificity)', fontsize=12, fontweight='bold')
        ax.set_ylabel('True Positive Rate (Sensitivity/Recall)', fontsize=12, fontweight='bold')
        ax.set_title(f'ROC Curve - {self.model_name}', fontsize=14, fontweight='bold')
        ax.legend(loc="lower right", fontsize=11)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ ROC Curve saved to: {save_path}")
        
        plt.show()
        return roc_auc
    
    def plot_precision_recall_curve(self, save_path=None):
        """Plot and save Precision-Recall curve"""
        if self.y_pred_proba is None:
            print("⚠️  Probability predictions required for PR curve!")
            return None
        
        # Handle both binary and multi-class probability formats
        if len(self.y_pred_proba.shape) > 1 and self.y_pred_proba.shape[1] > 1:
            proba = self.y_pred_proba[:, 1]
        else:
            proba = self.y_pred_proba
        
        precision, recall, thresholds = precision_recall_curve(self.y_true, proba)
        pr_auc = auc(recall, precision)
        
        fig, ax = plt.subplots(figsize=(9, 7))
        
        # Plot PR curve
        ax.plot(recall, precision, color='green', lw=3, 
               label=f'PR curve (AUC = {pr_auc:.4f})')
        ax.axhline(y=np.sum(self.y_true)/len(self.y_true), color='red', 
                  linestyle='--', lw=2, label='Random Classifier')
        
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.05])
        ax.set_xlabel('Recall', fontsize=12, fontweight='bold')
        ax.set_ylabel('Precision', fontsize=12, fontweight='bold')
        ax.set_title(f'Precision-Recall Curve - {self.model_name}', fontsize=14, fontweight='bold')
        ax.legend(loc="best", fontsize=11)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ Precision-Recall Curve saved to: {save_path}")
        
        plt.show()
        return pr_auc
    
    def plot_all_metrics(self, save_dir='./metrics_output'):
        """Plot all metrics in a single comprehensive figure"""
        fig = plt.figure(figsize=(16, 12))
        
        # 1. Metrics Bar Chart (top-left)
        ax1 = plt.subplot(2, 3, 1)
        self.calculate_metrics()
        metrics_to_plot = {k: v for k, v in self.metrics.items() if k != 'AUC-ROC'}
        colors = ['#2ecc71' if v > 0.8 else '#f39c12' if v > 0.6 else '#e74c3c' 
                 for v in metrics_to_plot.values()]
        bars = ax1.barh(list(metrics_to_plot.keys()), list(metrics_to_plot.values()), color=colors)
        ax1.set_xlim([0, 1])
        ax1.set_xlabel('Score', fontweight='bold')
        ax1.set_title('Performance Metrics', fontweight='bold', fontsize=12)
        
        # Add value labels
        for i, bar in enumerate(bars):
            width = bar.get_width()
            ax1.text(width, bar.get_y() + bar.get_height()/2, 
                    f'{width:.3f}', ha='left', va='center', fontweight='bold')
        
        # 2. Confusion Matrix (top-middle)
        ax2 = plt.subplot(2, 3, 2)
        cm = confusion_matrix(self.y_true, self.y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=['Negative', 'Positive'],
                   yticklabels=['Negative', 'Positive'],
                   cbar=False, ax=ax2, annot_kws={'size': 12})
        ax2.set_title('Confusion Matrix', fontweight='bold', fontsize=12)
        ax2.set_ylabel('True Label', fontweight='bold')
        ax2.set_xlabel('Predicted Label', fontweight='bold')
        
        # 3. Classification Metrics Comparison (top-right)
        ax3 = plt.subplot(2, 3, 3)
        class_metrics = ['Precision', 'Recall', 'F1 Score']
        class_values = [self.metrics['Precision'], self.metrics['Recall'], 
                       self.metrics['F1 Score']]
        colors_cm = ['#3498db', '#e74c3c', '#2ecc71']
        bars = ax3.bar(class_metrics, class_values, color=colors_cm, edgecolor='black', linewidth=1.5)
        ax3.set_ylim([0, 1.1])
        ax3.set_ylabel('Score', fontweight='bold')
        ax3.set_title('Key Classification Metrics', fontweight='bold', fontsize=12)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2, height,
                    f'{height:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # 4. ROC Curve (bottom-left)
        ax4 = plt.subplot(2, 3, 4)
        if self.y_pred_proba is not None:
            if len(self.y_pred_proba.shape) > 1 and self.y_pred_proba.shape[1] > 1:
                proba = self.y_pred_proba[:, 1]
            else:
                proba = self.y_pred_proba
            
            fpr, tpr, _ = roc_curve(self.y_true, proba)
            roc_auc = auc(fpr, tpr)
            
            ax4.plot(fpr, tpr, color='darkorange', lw=2.5, 
                    label=f'AUC = {roc_auc:.4f}')
            ax4.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', alpha=0.8)
            ax4.set_xlabel('False Positive Rate', fontweight='bold')
            ax4.set_ylabel('True Positive Rate', fontweight='bold')
            ax4.set_title('ROC Curve', fontweight='bold', fontsize=12)
            ax4.legend(fontsize=10)
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'Probabilities not available', 
                    ha='center', va='center', fontsize=12)
            ax4.set_title('ROC Curve (N/A)', fontweight='bold', fontsize=12)
        
        # 5. Precision-Recall Curve (bottom-middle)
        ax5 = plt.subplot(2, 3, 5)
        if self.y_pred_proba is not None:
            if len(self.y_pred_proba.shape) > 1 and self.y_pred_proba.shape[1] > 1:
                proba = self.y_pred_proba[:, 1]
            else:
                proba = self.y_pred_proba
            
            precision, recall, _ = precision_recall_curve(self.y_true, proba)
            pr_auc = auc(recall, precision)
            
            ax5.plot(recall, precision, color='green', lw=2.5, 
                    label=f'PR AUC = {pr_auc:.4f}')
            ax5.axhline(y=np.sum(self.y_true)/len(self.y_true), 
                       color='red', linestyle='--', lw=2, alpha=0.8)
            ax5.set_xlabel('Recall', fontweight='bold')
            ax5.set_ylabel('Precision', fontweight='bold')
            ax5.set_title('Precision-Recall Curve', fontweight='bold', fontsize=12)
            ax5.legend(fontsize=10)
            ax5.grid(True, alpha=0.3)
        else:
            ax5.text(0.5, 0.5, 'Probabilities not available', 
                    ha='center', va='center', fontsize=12)
            ax5.set_title('PR Curve (N/A)', fontweight='bold', fontsize=12)
        
        # 6. Prediction Distribution (bottom-right)
        ax6 = plt.subplot(2, 3, 6)
        if self.y_pred_proba is not None:
            if len(self.y_pred_proba.shape) > 1 and self.y_pred_proba.shape[1] > 1:
                proba = self.y_pred_proba[:, 1]
            else:
                proba = self.y_pred_proba
            
            ax6.hist(proba[self.y_true == 0], bins=30, alpha=0.6, 
                    label='Negative Class', color='blue', edgecolor='black')
            ax6.hist(proba[self.y_true == 1], bins=30, alpha=0.6, 
                    label='Positive Class', color='red', edgecolor='black')
            ax6.set_xlabel('Predicted Probability', fontweight='bold')
            ax6.set_ylabel('Frequency', fontweight='bold')
            ax6.set_title('Prediction Distribution', fontweight='bold', fontsize=12)
            ax6.legend(fontsize=10)
        else:
            ax6.text(0.5, 0.5, 'Probabilities not available', 
                    ha='center', va='center', fontsize=12)
        
        plt.suptitle(f'Complete Model Evaluation - {self.model_name}', 
                    fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        if save_dir:
            import os
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f'{self.model_name}_all_metrics.png')
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"✅ Complete metrics dashboard saved to: {save_path}")
        
        plt.show()
    
    def generate_summary_report(self):
        """Generate a text summary report"""
        self.calculate_metrics()
        
        report = f"""
{'='*70}
COMPLETE MODEL EVALUATION REPORT
{'='*70}

Model Name: {self.model_name}
Total Samples: {len(self.y_true)}
Positive Class: {np.sum(self.y_true)}
Negative Class: {len(self.y_true) - np.sum(self.y_true)}

CORE METRICS:
- Accuracy:       {self.metrics['Accuracy']:.4f}
- Precision:      {self.metrics['Precision']:.4f}
- Recall:         {self.metrics['Recall']:.4f}
- F1 Score:       {self.metrics['F1 Score']:.4f}

ADVANCED METRICS:
- Matthews Corr:  {self.metrics['Matthews CC']:.4f}
- Cohen's Kappa:  {self.metrics["Cohen's Kappa"]:.4f}
- AUC-ROC:        {self.metrics.get('AUC-ROC', 'N/A')}

INTERPRETATION:
"""
        
        # Interpret metrics
        acc = self.metrics['Accuracy']
        if acc > 0.9:
            report += "✅ Accuracy: Excellent (>90%)\n"
        elif acc > 0.8:
            report += "✅ Accuracy: Good (>80%)\n"
        elif acc > 0.7:
            report += "⚠️  Accuracy: Acceptable (>70%)\n"
        else:
            report += "❌ Accuracy: Poor (<70%)\n"
        
        f1 = self.metrics['F1 Score']
        if f1 > 0.8:
            report += "✅ F1 Score: Excellent\n"
        elif f1 > 0.6:
            report += "⚠️  F1 Score: Moderate\n"
        else:
            report += "❌ F1 Score: Low\n"
        
        report += "="*70 + "\n"
        
        return report


# ============================================================================
# EXAMPLE USAGE AND SAMPLE DATA GENERATION
# ============================================================================

def generate_sample_data(n_samples=1000, random_state=42):
    """
    Generate sample classification data for demonstration
    Simulates a scenario like: "Predict if user needs emission reduction recommendations"
    """
    np.random.seed(random_state)
    
    # Features
    X = np.random.randn(n_samples, 5)
    
    # Create target based on features with some noise
    y_true = (X[:, 0] + X[:, 1] > 0).astype(int)
    
    # Add some noise
    noise_idx = np.random.choice(n_samples, size=int(0.1 * n_samples), replace=False)
    y_true[noise_idx] = 1 - y_true[noise_idx]
    
    # Generate predictions (slightly imperfect)
    y_pred = y_true.copy()
    error_idx = np.random.choice(n_samples, size=int(0.15 * n_samples), replace=False)
    y_pred[error_idx] = 1 - y_pred[error_idx]
    
    # Generate probabilities
    y_pred_proba = np.random.rand(n_samples)
    y_pred_proba[y_true == 1] += 0.3  # Positive class should have higher proba
    y_pred_proba[y_true == 0] -= 0.3  # Negative class should have lower proba
    y_pred_proba = np.clip(y_pred_proba, 0, 1)
    
    return y_true, y_pred, y_pred_proba


def run_complete_evaluation(y_true, y_pred, y_pred_proba=None, model_name="Carbon Tracker Model"):
    """
    Run complete evaluation pipeline
    
    Args:
        y_true: Actual labels
        y_pred: Predicted labels
        y_pred_proba: Prediction probabilities (optional)
        model_name: Name of the model
    """
    print(f"\n🚀 Starting evaluation for: {model_name}")
    
    # Create evaluator
    evaluator = ModelEvaluator(y_true, y_pred, y_pred_proba, model_name)
    
    # Print metrics report
    evaluator.print_metrics_report()
    
    # Generate all visualizations
    print("\n📊 Generating visualizations...")
    evaluator.plot_all_metrics(save_dir='./model_metrics_output')
    
    # Print summary
    print(evaluator.generate_summary_report())
    
    return evaluator


if __name__ == "__main__":
    # Example usage with sample data
    print("\n" + "="*70)
    print("CARBON TRACKER - MODEL EVALUATION SYSTEM")
    print("="*70)
    
    # Generate sample data
    print("\n📈 Generating sample data for demonstration...")
    y_true, y_pred, y_pred_proba = generate_sample_data(n_samples=500)
    
    # Run evaluation
    evaluator = run_complete_evaluation(
        y_true, 
        y_pred, 
        y_pred_proba,
        model_name="Carbon Emission Predictor"
    )
    
    print("\n✅ Evaluation complete! Check ./model_metrics_output/ for visualizations.")
