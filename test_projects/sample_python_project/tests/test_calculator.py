"""
Unit tests for calculator modules.
"""

import pytest
import math
from src.calculator.basic_ops import BasicCalculator, CalculatorError
from src.calculator.advanced_ops import AdvancedCalculator, AdvancedCalculatorError


class TestBasicCalculator:
    """Test cases for BasicCalculator class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.calc = BasicCalculator()
    
    def test_addition(self):
        """Test addition operation."""
        assert self.calc.add(2, 3) == 5
        assert self.calc.add(-1, 1) == 0
        assert self.calc.add(0.1, 0.2) == pytest.approx(0.3)
        assert self.calc.add(-5, -3) == -8
    
    def test_subtraction(self):
        """Test subtraction operation."""
        assert self.calc.subtract(5, 3) == 2
        assert self.calc.subtract(1, 1) == 0
        assert self.calc.subtract(-5, -3) == -2
        assert self.calc.subtract(0.5, 0.2) == pytest.approx(0.3)
    
    def test_multiplication(self):
        """Test multiplication operation."""
        assert self.calc.multiply(3, 4) == 12
        assert self.calc.multiply(-2, 3) == -6
        assert self.calc.multiply(0, 100) == 0
        assert self.calc.multiply(0.5, 0.4) == pytest.approx(0.2)
    
    def test_division(self):
        """Test division operation."""
        assert self.calc.divide(10, 2) == 5
        assert self.calc.divide(-6, 3) == -2
        assert self.calc.divide(1, 3) == pytest.approx(0.3333333333333333)
        assert self.calc.divide(0, 5) == 0
    
    def test_division_by_zero(self):
        """Test division by zero raises appropriate error."""
        with pytest.raises(CalculatorError, match="Division by zero is not allowed"):
            self.calc.divide(5, 0)
    
    def test_operation_history(self):
        """Test that operations are recorded in history."""
        self.calc.add(2, 3)
        self.calc.multiply(4, 5)
        
        history = self.calc.get_history()
        assert len(history) == 2
        assert history[0]["operation"] == "add"
        assert history[0]["result"] == 5
        assert history[1]["operation"] == "multiply"
        assert history[1]["result"] == 20
    
    def test_last_result(self):
        """Test last result tracking."""
        self.calc.add(10, 5)
        assert self.calc.get_last_result() == 15
        
        self.calc.divide(20, 4)
        assert self.calc.get_last_result() == 5
    
    def test_clear_history(self):
        """Test history clearing functionality."""
        self.calc.add(1, 2)
        self.calc.subtract(5, 3)
        
        assert len(self.calc.get_history()) == 2
        
        self.calc.clear_history()
        assert len(self.calc.get_history()) == 0
        assert self.calc.get_last_result() == 0


class TestAdvancedCalculator:
    """Test cases for AdvancedCalculator class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.calc = AdvancedCalculator()
    
    def test_power(self):
        """Test power operation."""
        assert self.calc.power(2, 3) == 8
        assert self.calc.power(5, 0) == 1
        assert self.calc.power(4, 0.5) == 2
        assert self.calc.power(-2, 3) == -8
    
    def test_square_root(self):
        """Test square root operation."""
        assert self.calc.square_root(16) == 4
        assert self.calc.square_root(0) == 0
        assert self.calc.square_root(2) == pytest.approx(1.4142135624)
    
    def test_square_root_negative(self):
        """Test square root of negative number raises error."""
        with pytest.raises(AdvancedCalculatorError, 
                          match="Cannot calculate square root of negative number"):
            self.calc.square_root(-4)
    
    def test_nth_root(self):
        """Test nth root operation."""
        assert self.calc.nth_root(27, 3) == 3
        assert self.calc.nth_root(16, 4) == 2
        assert self.calc.nth_root(32, 5) == 2
    
    def test_nth_root_zero_degree(self):
        """Test nth root with zero degree raises error."""
        with pytest.raises(AdvancedCalculatorError, match="Root degree cannot be zero"):
            self.calc.nth_root(10, 0)
    
    def test_logarithm(self):
        """Test logarithm operations."""
        assert self.calc.logarithm(math.e) == pytest.approx(1)  # Natural log
        assert self.calc.logarithm(100, 10) == pytest.approx(2)  # Log base 10
        assert self.calc.logarithm(8, 2) == pytest.approx(3)  # Log base 2
    
    def test_logarithm_invalid_input(self):
        """Test logarithm with invalid inputs."""
        with pytest.raises(AdvancedCalculatorError, 
                          match="Logarithm undefined for non-positive numbers"):
            self.calc.logarithm(0)
        
        with pytest.raises(AdvancedCalculatorError, 
                          match="Logarithm undefined for non-positive numbers"):
            self.calc.logarithm(-5)
        
        with pytest.raises(AdvancedCalculatorError, match="Invalid logarithm base"):
            self.calc.logarithm(10, 1)
    
    def test_trigonometric_functions(self):
        """Test trigonometric functions."""
        # Test in radians (default)
        assert self.calc.sine(0) == 0
        assert self.calc.sine(math.pi/2) == pytest.approx(1)
        assert self.calc.cosine(0) == 1
        assert self.calc.cosine(math.pi) == pytest.approx(-1)
        assert self.calc.tangent(0) == 0
        assert self.calc.tangent(math.pi/4) == pytest.approx(1)
    
    def test_trigonometric_degrees_mode(self):
        """Test trigonometric functions in degrees mode."""
        self.calc.set_angle_mode("degrees")
        
        assert self.calc.sine(0) == 0
        assert self.calc.sine(90) == pytest.approx(1)
        assert self.calc.cosine(0) == 1
        assert self.calc.cosine(180) == pytest.approx(-1)
        assert self.calc.tangent(0) == 0
        assert self.calc.tangent(45) == pytest.approx(1)
    
    def test_factorial(self):
        """Test factorial operation."""
        assert self.calc.factorial(0) == 1
        assert self.calc.factorial(1) == 1
        assert self.calc.factorial(5) == 120
        assert self.calc.factorial(10) == 3628800
    
    def test_factorial_invalid_input(self):
        """Test factorial with invalid inputs."""
        with pytest.raises(AdvancedCalculatorError, 
                          match="Factorial is only defined for non-negative integers"):
            self.calc.factorial(-1)
        
        with pytest.raises(AdvancedCalculatorError, 
                          match="Factorial is only defined for non-negative integers"):
            self.calc.factorial(3.5)
    
    def test_precision_setting(self):
        """Test precision setting functionality."""
        self.calc.set_precision(2)
        result = self.calc.square_root(2)
        assert result == 1.41
        
        self.calc.set_precision(4)
        result = self.calc.square_root(2)
        assert result == 1.4142
    
    def test_precision_invalid(self):
        """Test invalid precision setting."""
        with pytest.raises(AdvancedCalculatorError, match="Precision must be non-negative"):
            self.calc.set_precision(-1)
    
    def test_angle_mode_setting(self):
        """Test angle mode setting."""
        self.calc.set_angle_mode("degrees")
        assert self.calc.angle_mode == "degrees"
        
        self.calc.set_angle_mode("radians")
        assert self.calc.angle_mode == "radians"
    
    def test_angle_mode_invalid(self):
        """Test invalid angle mode setting."""
        with pytest.raises(AdvancedCalculatorError, 
                          match="Angle mode must be 'radians' or 'degrees'"):
            self.calc.set_angle_mode("invalid")


class TestCalculatorIntegration:
    """Integration tests using both calculator classes."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.basic_calc = BasicCalculator()
        self.advanced_calc = AdvancedCalculator()
    
    def test_complex_calculation(self):
        """Test a complex calculation using both calculators."""
        # Calculate (2 + 3) * 4^2 / sqrt(16)
        step1 = self.basic_calc.add(2, 3)  # 5
        step2 = self.advanced_calc.power(4, 2)  # 16
        step3 = self.basic_calc.multiply(step1, step2)  # 80
        step4 = self.advanced_calc.square_root(16)  # 4
        result = self.basic_calc.divide(step3, step4)  # 20
        
        assert result == 20
    
    def test_scientific_calculation(self):
        """Test scientific calculation with trigonometry."""
        # Calculate sin(π/4) + cos(π/4)
        self.advanced_calc.set_angle_mode("radians")
        
        sin_result = self.advanced_calc.sine(math.pi/4)
        cos_result = self.advanced_calc.cosine(math.pi/4)
        total = self.basic_calc.add(sin_result, cos_result)
        
        expected = math.sqrt(2)  # sin(π/4) + cos(π/4) = √2/2 + √2/2 = √2
        assert total == pytest.approx(expected, rel=1e-9)
