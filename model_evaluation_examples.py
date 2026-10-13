"""
Practical Examples for Model Evaluation
========================================
Real-world usage examples for Carbon Tracker model evaluation

Run any of these examples:
    python model_evaluation_examples.py
"""

import numpy as np
from model_evaluation import ModelEvaluator, run_complete_evaluation


# ============================================================================
# EXAMPLE 1: Vehicle Type Classification
# ============================================================================
def example_1_vehicle_type_classification():
    """
    Predict if a route's vehicle type should be switched to a more eco-friendly option
    1 = Should Switch (EV/Public Transport)
    0 = Already Eco-Friendly (Bike/Walk/Transit)
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: Vehicle Type Classification")
    print("Predicting if user should switch to eco-friendly transport")
    print("="*70)
    
    # 100 actual labels
    y_true = np.array([1, 0, 1, 1, 0, 0, 1, 1, 0, 1] * 10)
    
    # Model predictions (slightly imperfect)
    y_pred = np.array([1, 0, 1, 0, 0, 0, 1, 1, 1, 1] * 10)
    
    # Probability scores
    y_pred_proba = np.array([
        0.92, 0.15, 0.88, 0.45, 0.22, 0.18, 0.91, 0.87, 0.65, 0.93,
        0.89, 0.12, 0.85, 0.40, 0.20, 0.15, 0.88, 0.90, 0.62, 0.95
    ] * 5)
    
    run_complete_evaluation(y_true, y_pred, y_pred_proba, 
                           model_name="Vehicle Type Recommender")


# ============================================================================
# EXAMPLE 2: High Emission Route Detection
# ============================================================================
def example_2_emission_level_classification():
    """
    Classify routes as HIGH or LOW emission based on traffic and distance
    1 = High Emission (Heavy traffic, long distance)
    0 = Low Emission (Light traffic, short distance)
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: Emission Level Classification")
    print("Detecting high-emission routes for optimization")
    print("="*70)
    
    np.random.seed(42)
    n_samples = 200
    
    # Real labels
    y_true = np.random.binomial(1, 0.4, n_samples)
    
    # Predictions with 80% accuracy
    y_pred = y_true.copy()
    errors = np.random.choice(n_samples, size=int(0.2 * n_samples), replace=False)
    y_pred[errors] = 1 - y_pred[errors]
    
    # Probabilities
    y_pred_proba = np.random.uniform(0, 1, n_samples)
    y_pred_proba[y_true == 1] = np.random.uniform(0.6, 1, np.sum(y_true == 1))
    y_pred_proba[y_true == 0] = np.random.uniform(0, 0.4, np.sum(y_true == 0))
    
    evaluator = ModelEvaluator(y_true, y_pred, y_pred_proba, 
                              model_name="Emission Level Detector")
    evaluator.plot_all_metrics(save_dir='./example2_metrics')
    evaluator.print_metrics_report()


# ============================================================================
# EXAMPLE 3: User Engagement Prediction
# ============================================================================
def example_3_user_engagement():
    """
    Predict if a user will actively reduce emissions or stay inactive
    1 = Will Reduce Emissions (Active user)
    0 = Will Stay Inactive
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: User Engagement Prediction")
    print("Predicting user participation in emission reduction")
    print("="*70)
    
    np.random.seed(123)
    n_samples = 300
    
    # Create realistic data (30% active users)
    y_true = np.random.binomial(1, 0.3, n_samples)
    
    # Model performance: 82% accuracy
    y_pred = y_true.copy()
    errors = np.random.choice(n_samples, size=int(0.18 * n_samples), replace=False)
    y_pred[errors] = 1 - y_pred[errors]
    
    # Probabilities
    y_pred_proba = np.random.uniform(0.3, 0.7, n_samples)
    y_pred_proba[y_true == 1] = np.random.uniform(0.65, 1, np.sum(y_true == 1))
    y_pred_proba[y_true == 0] = np.random.uniform(0, 0.35, np.sum(y_true == 0))
    
    evaluator = ModelEvaluator(y_true, y_pred, y_pred_proba, 
                              model_name="User Engagement Predictor")
    evaluator.plot_all_metrics(save_dir='./example3_metrics')
    evaluator.print_metrics_report()


# ============================================================================
# EXAMPLE 4: Route Optimization Success
# ============================================================================
def example_4_route_optimization():
    """
    Predict if an optimized route will save significant emissions (>15%)
    1 = Significant Savings Expected
    0 = Minimal Savings
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: Route Optimization Prediction")
    print("Predicting optimization success rate")
    print("="*70)
    
    np.random.seed(456)
    n_samples = 150
    
    # 60% of routes can be significantly optimized
    y_true = np.random.binomial(1, 0.6, n_samples)
    
    # Model with 85% accuracy
    y_pred = y_true.copy()
    errors = np.random.choice(n_samples, size=int(0.15 * n_samples), replace=False)
    y_pred[errors] = 1 - y_pred[errors]
    
    # Very confident probabilities
    y_pred_proba = np.random.uniform(0, 1, n_samples)
    y_pred_proba[y_true == 1] = np.random.uniform(0.7, 1, np.sum(y_true == 1))
    y_pred_proba[y_true == 0] = np.random.uniform(0, 0.3, np.sum(y_true == 0))
    
    run_complete_evaluation(y_true, y_pred, y_pred_proba, 
                           model_name="Route Optimization Predictor")


# ============================================================================
# EXAMPLE 5: Traffic Congestion Detection
# ============================================================================
def example_5_traffic_detection():
    """
    Predict if a route will have heavy traffic during travel time
    1 = Heavy Traffic Expected
    0 = Normal Traffic
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: Traffic Congestion Detection")
    print("Predicting traffic conditions for better route selection")
    print("="*70)
    
    np.random.seed(789)
    n_samples = 250
    
    # 45% of predicted time slots will have heavy traffic
    y_true = np.random.binomial(1, 0.45, n_samples)
    
    # Model with 88% accuracy
    y_pred = y_true.copy()
    errors = np.random.choice(n_samples, size=int(0.12 * n_samples), replace=False)
    y_pred[errors] = 1 - y_pred[errors]
    
    # Probabilities
    y_pred_proba = np.random.uniform(0.2, 0.8, n_samples)
    y_pred_proba[y_true == 1] = np.random.uniform(0.65, 1, np.sum(y_true == 1))
    y_pred_proba[y_true == 0] = np.random.uniform(0, 0.35, np.sum(y_true == 0))
    
    evaluator = ModelEvaluator(y_true, y_pred, y_pred_proba, 
                              model_name="Traffic Congestion Detector")
    evaluator.plot_all_metrics(save_dir='./example5_metrics')
    evaluator.print_metrics_report()


# ============================================================================
# EXAMPLE 6: Leaderboard Prediction
# ============================================================================
def example_6_leaderboard_prediction():
    """
    Predict if a user will make it to the top 10% of leaderboard
    1 = Will Reach Top 10%
    0 = Will Not Reach Top 10%
    """
    print("\n" + "="*70)
    print("EXAMPLE 6: Leaderboard Achievement Prediction")
    print("Predicting user's achievement of top rankings")
    print("="*70)
    
    np.random.seed(101)
    n_samples = 350
    
    # Only 10% will make top rankings
    y_true = np.random.binomial(1, 0.1, n_samples)
    
    # Model with 92% accuracy
    y_pred = y_true.copy()
    errors = np.random.choice(n_samples, size=int(0.08 * n_samples), replace=False)
    y_pred[errors] = 1 - y_pred[errors]
    
    # Probabilities
    y_pred_proba = np.random.uniform(0.2, 0.8, n_samples)
    y_pred_proba[y_true == 1] = np.random.uniform(0.75, 1, np.sum(y_true == 1))
    y_pred_proba[y_true == 0] = np.random.uniform(0, 0.25, np.sum(y_true == 0))
    
    run_complete_evaluation(y_true, y_pred, y_pred_proba, 
                           model_name="Leaderboard Achievement Predictor")


# ============================================================================
# EXAMPLE 7: Carbon Offset Recommendation
# ============================================================================
def example_7_offset_recommendation():
    """
    Predict if a user should purchase carbon offsets for their travel
    1 = Should Purchase Offsets
    0 = Already Low Emissions
    """
    print("\n" + "="*70)
    print("EXAMPLE 7: Carbon Offset Recommendation")
    print("Recommending carbon offset purchases")
    print("="*70)
    
    np.random.seed(202)
    n_samples = 400
    
    # 35% need offset recommendations
    y_true = np.random.binomial(1, 0.35, n_samples)
    
    # Model with 80% accuracy
    y_pred = y_true.copy()
    errors = np.random.choice(n_samples, size=int(0.20 * n_samples), replace=False)
    y_pred[errors] = 1 - y_pred[errors]
    
    # Probabilities
    y_pred_proba = np.random.uniform(0.3, 0.7, n_samples)
    y_pred_proba[y_true == 1] = np.random.uniform(0.6, 1, np.sum(y_true == 1))
    y_pred_proba[y_true == 0] = np.random.uniform(0, 0.4, np.sum(y_true == 0))
    
    evaluator = ModelEvaluator(y_true, y_pred, y_pred_proba, 
                              model_name="Carbon Offset Recommender")
    evaluator.plot_all_metrics(save_dir='./example7_metrics')
    evaluator.print_metrics_report()


# ============================================================================
# EXAMPLE 8: Combined Comparison
# ============================================================================
def example_8_model_comparison():
    """
    Compare multiple models on the same task
    """
    print("\n" + "="*70)
    print("EXAMPLE 8: Model Comparison")
    print("Comparing 3 different models on same task")
    print("="*70)
    
    np.random.seed(303)
    n_samples = 200
    
    # Ground truth
    y_true = np.random.binomial(1, 0.5, n_samples)
    
    # Model 1: 78% accuracy
    y_pred_1 = y_true.copy()
    errors_1 = np.random.choice(n_samples, size=int(0.22 * n_samples), replace=False)
    y_pred_1[errors_1] = 1 - y_pred_1[errors_1]
    y_proba_1 = np.random.uniform(0, 1, n_samples)
    y_proba_1[y_true == 1] = np.random.uniform(0.5, 1, np.sum(y_true == 1))
    
    # Model 2: 85% accuracy
    y_pred_2 = y_true.copy()
    errors_2 = np.random.choice(n_samples, size=int(0.15 * n_samples), replace=False)
    y_pred_2[errors_2] = 1 - y_pred_2[errors_2]
    y_proba_2 = np.random.uniform(0, 1, n_samples)
    y_proba_2[y_true == 1] = np.random.uniform(0.6, 1, np.sum(y_true == 1))
    
    # Model 3: 92% accuracy
    y_pred_3 = y_true.copy()
    errors_3 = np.random.choice(n_samples, size=int(0.08 * n_samples), replace=False)
    y_pred_3[errors_3] = 1 - y_pred_3[errors_3]
    y_proba_3 = np.random.uniform(0, 1, n_samples)
    y_proba_3[y_true == 1] = np.random.uniform(0.7, 1, np.sum(y_true == 1))
    
    # Evaluate all three
    for name, pred, proba in [
        ("Model A (Simple)", y_pred_1, y_proba_1),
        ("Model B (Intermediate)", y_pred_2, y_proba_2),
        ("Model C (Advanced)", y_pred_3, y_proba_3)
    ]:
        evaluator = ModelEvaluator(y_true, pred, proba, model_name=name)
        print("\n" + "-"*70)
        evaluator.print_metrics_report()


# ============================================================================
# MAIN: Run all examples
# ============================================================================
def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("CARBON TRACKER - MODEL EVALUATION EXAMPLES")
    print("="*70)
    print("\n📊 Running 8 practical evaluation examples...\n")
    
    try:
        example_1_vehicle_type_classification()
        example_2_emission_level_classification()
        example_3_user_engagement()
        example_4_route_optimization()
        example_5_traffic_detection()
        example_6_leaderboard_prediction()
        example_7_offset_recommendation()
        example_8_model_comparison()
        
        print("\n" + "="*70)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\n📁 Check these directories for visualizations:")
        print("   • ./model_metrics_output/")
        print("   • ./example2_metrics/")
        print("   • ./example3_metrics/")
        print("   • ./example5_metrics/")
        print("   • ./example7_metrics/")
        
    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
